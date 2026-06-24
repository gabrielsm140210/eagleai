import os
import streamlit as st
from dotenv import load_dotenv
import hashlib
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager
import warnings 

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_community.tools.tavily_search import TavilySearchResults

st.set_page_config(page_title="Eagle AI", page_icon="🦅", layout="centered")

COR_PRIMARIA = "#111111"
COR_SECUNDARIA = "#FFFFFF"
COR_DESTAQUE = "#444444"

st.markdown(f"""
<style>
    body, .stApp {{
        background-color: #0a0a0a;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {COR_PRIMARIA};
    }}
    section[data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    .main-header {{
        background: linear-gradient(90deg, #111111 0%, #2a2a2a 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 6px solid {COR_SECUNDARIA};
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 1.6rem;
    }}
    .main-header p {{
        color: #CCCCCC;
        margin: 0.3rem 0 0 0;
    }}
    .status-ok {{
        background-color: rgba(46, 204, 113, 0.15);
        color: #1B8A4B;
        border: 1px solid rgba(46, 204, 113, 0.4);
        padding: 0.4rem 0.7rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }}
    .status-error {{
        background-color: rgba(176, 0, 32, 0.12);
        color: #B00020;
        border: 1px solid rgba(176, 0, 32, 0.4);
        padding: 0.4rem 0.7rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }}
</style>
""", unsafe_allow_html=True)

cookies = EncryptedCookieManager(prefix="eagleai_", password="eagle_secret_key_2025_long_enough")
if not cookies.ready():
    st.warning("Carregando componentes de segurança...")
    st.stop()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def registrar_usuario(username, senha):
    try:
        supabase.table("usuarios").insert({
            "username": username,
            "senha_hash": hash_senha(senha)
        }).execute()
        return True, "Conta criada com sucesso!"
    except Exception as e:
        return False, "Usuário já existe ou erro ao criar conta."

def login_usuario(username, senha):
    try:
        resultado = supabase.table("usuarios").select("*").eq("username", username).eq("senha_hash", hash_senha(senha)).execute()
        if resultado.data:
            return True, resultado.data[0]["id"]
        return False, None
    except Exception:
        return False, None

def salvar_mensagem(usuario_id, role, conteudo):
    try:
        supabase.table("historico").insert({
            "usuario_id": usuario_id,
            "role": role,
            "conteudo": conteudo
        }).execute()
    except Exception:
        pass

def carregar_historico(usuario_id):
    try:
        resultado = supabase.table("historico").select("*").eq("usuario_id", usuario_id).order("criado_em").execute()
        return [{"role": r["role"], "content": r["conteudo"]} for r in resultado.data]
    except Exception:
        return []

def limpar_historico(usuario_id):
    try:
        supabase.table("historico").delete().eq("usuario_id", usuario_id).execute()
    except Exception:
        pass

if "logout_efetuado" not in st.session_state:
    st.session_state.logout_efetuado = False

if "usuario_id" not in st.session_state and not st.session_state.logout_efetuado:
    cookie_uid = cookies.get("usuario_id")
    cookie_username = cookies.get("username")
    if cookie_uid and cookie_username:
        st.session_state.usuario_id = cookie_uid
        st.session_state.username = cookie_username
        st.session_state.messages = carregar_historico(cookie_uid)

if "usuario_id" not in st.session_state:
    st.markdown("""
    <div style='text-align:center; margin-top: 2rem;'>
        <h1 style='color:#FFFFFF; font-size: 2.5rem;'>🦅 Eagle AI</h1>
        <p style='color:#CCCCCC;'>Assistente inteligente com busca em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    aba = st.radio("", ["Entrar", "Criar conta"], horizontal=True)

    if aba == "Entrar":
        st.markdown("### Login")
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        lembrar = st.checkbox("Lembre de mim")
        if st.button("Entrar", use_container_width=True):
            if username and senha:
                ok, uid = login_usuario(username, senha)
                if ok:
                    st.session_state.usuario_id = uid
                    st.session_state.username = username
                    st.session_state.messages = carregar_historico(uid)
                    if lembrar:
                        cookies["usuario_id"] = str(uid)
                        cookies["username"] = str(username)
                        cookies.save()
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            else:
                st.warning("Preencha todos os campos.")

    else:
        st.markdown("### Criar conta")
        novo_user = st.text_input("Escolha um usuário")
        nova_senha = st.text_input("Escolha uma senha", type="password")
        if st.button("Criar conta", use_container_width=True):
            if novo_user and nova_senha:
                ok, msg = registrar_usuario(novo_user, nova_senha)
                if ok:
                    st.success(msg + " Agora faça login.")
                else:
                    st.error(msg)
            else:
                st.warning("Preencha todos os campos.")

    st.markdown(
        "<div style='text-align:center; color:gray; font-size:0.8rem; margin-top:3rem;'>"
        "🦅 Eagle AI — Feito por Gabriel S. Monteiro, Engenheiro e Desenvolvedor de Software"
        "</div>",
        unsafe_allow_html=True
    )
    st.stop()

st.markdown("""
<div class="main-header">
    <h1>🦅 Eagle AI</h1>
    <p>Assistente inteligente com busca em tempo real na web</p>
</div>
""", unsafe_allow_html=True)

st.write("Pergunte qualquer coisa. A Eagle AI busca informações atualizadas na web antes de responder.")

with st.sidebar:
    st.image("logo.jpg", use_container_width=True)
    st.markdown("---")

    st.markdown(f"👤 **Usuário:** {st.session_state.username}")
    st.markdown("---")

    st.markdown("⚡ **Modo de Resposta**")
    modo_velocidade = st.selectbox(
        "Escolha a velocidade da IA:",
        ["Águia Veloz (Mais Rápido ⚡)", "Águia Suprema (Mais Inteligente 🧠)"]
    )
    
    if modo_velocidade == "Águia Veloz (Mais Rápido ⚡)":
        modelo_selecionado = "meta/llama-3.1-8b-instruct"
        max_tokens_modo = 400
    else:
        modelo_selecionado = "meta/llama-3.3-70b-instruct"
        max_tokens_modo = 800

    st.markdown("---")

    st.markdown("#### 📋 Sobre o projeto")
    st.markdown(f"**🧠 Modelo ativo:** `{modelo_selecionado}`")
    st.markdown("**🌐 Busca na web:** Tavily Search API")
    st.markdown("**⚙️ Arquitetura:** LLM + Tool Calling")

    st.markdown("---")
    st.markdown("#### 👨‍💻 Desenvolvedor")
    st.markdown("**Feito por:** Gabriel S. Monteiro")
    st.markdown("** Engenheiro e Desenvolvedor de Software**")

    st.markdown("---")
    st.markdown("#### 📊 Status do Sistema")
    
    status_placeholder = st.empty()

    st.markdown("---")
    if st.button("🗑️ Limpar Conversa"):
        limpar_historico(st.session_state.usuario_id)
        st.session_state.messages = []
        st.rerun()
        
    if st.button("🚪 Sair"):
        if "usuario_id" in cookies:
            del cookies["usuario_id"]
        if "username" in cookies:
            del cookies["username"]
        cookies.save()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.logout_efetuado = True
        st.rerun()

nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
tavily_api_key = os.environ.get("TAVILY_API_KEY")

if not nvidia_api_key:
    try:
        if "NVIDIA_API_KEY" in st.secrets:
            nvidia_api_key = st.secrets["NVIDIA_API_KEY"]
    except Exception:
        pass

if not tavily_api_key:
    try:
        if "TAVILY_API_KEY" in st.secrets:
            tavily_api_key = st.secrets["TAVILY_API_KEY"]
    except Exception:
        pass

if not nvidia_api_key or not tavily_api_key:
    with status_placeholder.container():
        st.markdown(
            f'<div class="status-{"ok" if nvidia_api_key else "error"}">'
            f'{"🟢" if nvidia_api_key else "🔴"} IA (NVIDIA) '
            f'{"conectada" if nvidia_api_key else "não conectada"}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="status-{"ok" if tavily_api_key else "error"}">'
            f'{"🟢" if tavily_api_key else "🔴"} Busca web (Tavily) '
            f'{"conectada" if tavily_api_key else "não conectada"}</div>',
            unsafe_allow_html=True
        )
    st.info(
        "Adicione NVIDIA_API_KEY e TAVILY_API_KEY no arquivo .env (local) "
        "ou nos Secrets do Streamlit (deploy).",
        icon="🔑"
    )
    st.stop()

os.environ["TAVILY_API_KEY"] = tavily_api_key

try:
    busca_web = TavilySearchResults(max_results=5)
except Exception as e:
    with status_placeholder.container():
        st.markdown('<div class="status-error">🔴 Erro ao iniciar busca web</div>', unsafe_allow_html=True)
    st.error(f"Erro ao iniciar a ferramenta de busca (Tavily): {e}")
    st.stop()

try:
    llm = ChatNVIDIA(
        model=modelo_selecionado,
        nvidia_api_key=nvidia_api_key,
        temperature=0.3,
        max_tokens=max_tokens_modo
    )
except Exception as e:
    with status_placeholder.container():
        st.markdown('<div class="status-error">🔴 IA não conectada</div>', unsafe_allow_html=True)
    st.error(f"Erro ao conectar com a API da NVIDIA: {e}")
    st.stop()

with status_placeholder.container():
    st.markdown('<div class="status-ok">🟢 IA (NVIDIA) conectada</div>', unsafe_allow_html=True)
    st.markdown('<div class="status-ok">🟢 Busca web (Tavily) conectada</div>', unsafe_allow_html=True)

template_prompt = """
Você é a Eagle AI, um assistente de inteligência artificial criado por Gabriel S.
Monteiro (Engenheiro e Desenvolvedor de Software).

Resultados de busca na web (podem estar vazios se não foram necessários):
---------------------
{context}
---------------------

Instruções:
- Se os resultados da busca forem relevantes, use-os para enriquecer sua resposta e cite a fonte.
- Se a pergunta for simples ou você já souber a resposta com segurança, responda com seu próprio conhecimento.
- Se for usar buscas, বুকে por fontes recentes, ou seja, de 2025 em diante.
- Nunca invente dados, datas ou estatísticas. Se não tiver certeza, diga isso claramente.
- Seja direto: evite textos longos desnecessários.

Pergunta do usuário: {question}

ATENÇÃO: O idioma da pergunta acima é {idioma}. Você DEVE responder OBRIGATORIAMENTE nesse idioma. Não responda em nenhum outro idioma.
Resposta da Eagle AI:
"""

prompt = ChatPromptTemplate.from_template(template_prompt)
cadeia_resposta = prompt | llm | StrOutputParser()

if "messages" not in st.session_state:
    st.session_state.messages = carregar_historico(st.session_state.usuario_id)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt_usuario := st.chat_input("Pergunte qualquer coisa..."):
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    salvar_mensagem(st.session_state.usuario_id, "user", prompt_usuario)
    with st.chat_message("user"):
        st.write(prompt_usuario)

    with st.chat_message("assistant"):
        try:
            try:
                from langdetect import detect
                idioma_cod = detect(prompt_usuario)
                idioma = "português" if idioma_cod == "pt" else "inglês" if idioma_cod == "en" else "espanhol" if idioma_cod == "es" else "português"
            except Exception:
                idioma = "português"

            decisao_prompt = f"""Você decide se uma pergunta precisa de busca na web.
Responda APENAS com "SIM" ou "NAO". Sem justificativas.
Pergunta: {prompt_usuario}
Resposta:"""

            decisao = llm.invoke(decisao_prompt, max_tokens=2).content.strip().upper()
            precisa_buscar = "SIM" in decisao

            if precisa_buscar:
                with st.spinner("🔎 Buscando na web..."):
                    resultados = busca_web.invoke({"query": prompt_usuario})
                    contexto = "\n\n".join(
                        f"Fonte: {r.get('url', 'desconhecida')}\nConteúdo: {r.get('content', '')}"
                        for r in resultados
                    )
            else:
                contexto = "Nenhuma busca realizada. Use seu próprio conhecimento."

            with st.spinner("🦅 Gerando resposta..."):
                resposta = cadeia_resposta.invoke({
                    "context": contexto,
                    "question": prompt_usuario,
                    "idioma": idioma
                })

            st.write(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            salvar_mensagem(st.session_state.usuario_id, "assistant", resposta)

        except Exception as e:
            erro_msg = f"Erro ao processar sua pergunta: {e}"
            st.error(erro_msg)
            st.session_state.messages.append({"role": "assistant", "content": erro_msg})

st.markdown(
    "<div style='text-align:center; color:gray; font-size:0.8rem; margin-top:2rem;'>"
    "🦅 Eagle AI — Feito por Gabriel S. Monteiro, Engenheiro e Desenvolvedor de Software"
    "</div>",
    unsafe_allow_html=True
)
