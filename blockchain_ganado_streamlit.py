import streamlit as st
import hashlib
import json
import secrets
import random
from time import time
from datetime import date

# ------------------------ Clases Base ------------------------ #

class Wallet:
    def __init__(self, name, balance=10000.0):
        self.name = name
        self.private_key = secrets.token_hex(16)
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()
        self.balance = balance

class CattleBatch:
    def __init__(self, productor, cantidad, raza, ubicacion):
        self.productor = productor
        self.cantidad = cantidad  
        self.raza = raza
        self.ubicacion = ubicacion
        self.timestamp = time()

class FuturoGanado:
    def __init__(self, productor, lote_index, cantidad, fecha_entrega):
        self.productor = productor
        self.lote_index = lote_index
        self.cantidad = cantidad  
        self.fecha_entrega = fecha_entrega
        self.ofertas = []
        self.adjudicado = None

    def agregar_oferta(self, cliente, monto):
        self.ofertas.append((cliente, monto))

    def mejor_oferta(self):
        return max(self.ofertas, key=lambda x: x[1]) if self.ofertas else None

    def adjudicar_contrato(self):
        best = self.mejor_oferta()
        if best:
            self.adjudicado = best

class Block:
    def __init__(self, index, data, timestamp, previous_hash, nonce=0):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'data': self.data,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class CattleBlockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, {'info': 'Genesis Ganado'}, time(), '0')
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        block = Block(len(self.chain), transaction, time(), self.last_block.hash)
        while not block.hash.startswith('0000'):
            block.nonce += 1
            block.hash = block.compute_hash()
        self.chain.append(block)
        return block

# ------------------------ Interfaz Streamlit ------------------------ #

st.set_page_config(page_title="Blockchain Ganadero", layout="wide")
st.title("🐄 Simulador Blockchain Ganadero")

if 'chain' not in st.session_state:
    st.session_state.chain = CattleBlockchain()
    st.session_state.wallets = {}
    st.session_state.lotes = []
    st.session_state.futuros = []
    st.session_state.minado_por = {}

col1, col2, col3 = st.columns(3)

# Productores
with col1:
    st.header("👨‍🌾 Productores")
    nombre = st.text_input("Productor", key="prod_nombre")
    cantidad = st.number_input("Cabezas", min_value=1, step=1, key="prod_cant")
    raza = st.text_input("Raza", key="prod_raza")
    ubi = st.text_input("Ubicación", key="prod_ubi")
    if st.button("Registrar lote"):
        st.session_state.lotes.append((nombre, cantidad, raza, ubi))
        st.success("Lote registrado")
    st.subheader("Contrato Futuro")
    if st.session_state.lotes:
        opts = [f"Lote#{i} {p} ({c} cabezas)" 
                for i,(p,c,_,_) in enumerate(st.session_state.lotes)]
        sel = st.selectbox("Seleccione lote", opts, key="f_lote")
        idx = opts.index(sel)
        c_fut = st.number_input("Cantidad futura", min_value=1, step=1, key="f_cant")
        f_ent = st.date_input("Fecha entrega", key="f_fecha")
        if st.button("Emitir contrato"):
            prod,_,_,_ = st.session_state.lotes[idx]
            stu = sum(f[1] for f in st.session_state.futuros if f[0]==prod and f[2]==idx)
            if stu + c_fut <= st.session_state.lotes[idx][1]:
                st.session_state.futuros.append((prod, c_fut, idx, f_ent.isoformat(), [], None))
                st.success("Contrato creado")
            else:
                st.warning("Supera stock")

# Mineros/Compradores
with col2:
    st.header("⛏️ Mineros/Compradores")
    nombre2 = st.text_input("Nombre", key="w_name")
    bal = st.number_input("Saldo", min_value=0.0, value=1000.0, key="w_bal")
    if st.button("Crear Wallet"):
        st.session_state.wallets[nombre2] = bal
        st.success("Wallet lista")
    if st.button("Minar bloque vacío"):
        m = random.choice(list(st.session_state.wallets.keys()) or [""])
        st.session_state.minado_por[m] = st.session_state.minado_por.get(m,0)+1
        st.success(f"Minado por {m}")

# Ofertas
with col3:
    st.header("🛒 Ofertas")
    for i,(prod,c_fut,idx,fecha,ofs,adj) in enumerate(st.session_state.futuros):
        st.write(f"Contrato#{i} {prod}-{c_fut} cabezas entrega {fecha}")
        if not adj:
            compr = st.selectbox(f"Comprador #{i}", list(st.session_state.wallets.keys()), key=f"cb{i}")
            monto = st.number_input(f"Monto #{i}", min_value=1.0, max_value=st.session_state.wallets.get(compr,0), step=1.0, key=f"mo{i}")
            if st.button("Ofertar", key=f"of{i}"):
                ofs.append((compr,monto))
                st.success("Oferta lista")
            if len(st.session_state.wallets)>=3 and st.button("Adjudicar", key=f"ad{i}"):
                mejor = max(ofs, key=lambda x:x[1])
                st.session_state.futuros[i] = (prod,c_fut,idx,fecha,ofs,mejor)
                cliente,mt = mejor
                st.session_state.wallets[cliente] -= mt
                bono=mt*0.1
                st.session_state.wallets[compr] += bono
                st.session_state.wallets[prod] = st.session_state.wallets.get(prod,0)+mt*0.9
                st.success(f"Adjudicado a {cliente}")

st.subheader("📊 Contratos Adjudicados")
for prod,c_fut,idx,fecha,ofs,adj in st.session_state.futuros:
    if adj:
        st.write(prod, "→", adj[0], "$", adj[1])

st.subheader("🏆 Ranking Mineros")
for m,v in st.session_state.minado_por.items():
    st.write(m, v)

st.subheader("💰 Wallets")
for w,b in st.session_state.wallets.items():
    st.write(w, b)
