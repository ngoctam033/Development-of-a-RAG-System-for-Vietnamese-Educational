import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from rag_pipeline.llm.llm import GeminiGenerator
from rag_pipeline.generation.answer_generator import answer_question
from rag_pipeline.retrieval.vector_store import load_vector_store
import logging

from config.llm_api_config import GEMINI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.title("Chatbot hỗ trợ học tập 🎓")
vector_store = load_vector_store()
if "messages" not in st.session_state:
    st.session_state.messages = []

generator = GeminiGenerator(api_key=GEMINI_API_KEY)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Nhập câu hỏi...")

if question:
    logger.info(f"User question: {question}")
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    answer = answer_question(question, vector_store, generator, top_k=100)["answer"]
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)