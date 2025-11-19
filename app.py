# app.py
import streamlit as st
import pandas as pd

# Load products
def load_products():
    return pd.read_csv("products.csv")

# Page configuration
st.set_page_config(page_title="Budget Mission App", layout="wide")

# Session State initialization
if "mission" not in st.session_state:
    st.session_state.mission = None
if "budget" not in st.session_state:
    st.session_state.budget = None
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "result_image" not in st.session_state:
    st.session_state.result_image = None

# --- START SCREEN ---
def start_screen():
    st.title("🎯 미션 선택하기")
    st.write("3가지 미션 중 하나를 선택하여 예산을 결정하세요.")

    missions = {
        "미션 1 - 기본": 10000,
        "미션 2 - 중간": 20000,
        "미션 3 - 챌린지": 30000,
    }

    mission = st.radio("미션 선택", list(missions.keys()))

    if st.button("선택 완료 → 쇼핑 화면 이동"):
        st.session_state.mission = mission
        st.session_state.budget = missions[mission]
        st.switch_page("app.py")

# --- SHOPPING SCREEN ---
def shopping_screen():
    st.title("🛒 쇼핑하기")
    st.write(f"현재 미션: **{st.session_state.mission}**, 예산: **{st.session_state.budget}원**")

    df = load_products()

    categories = df["category"].unique()

    selected_category = st.selectbox("카테고리 선택", categories)
    filtered = df[df["category"] == selected_category]

    for _, row in filtered.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{row['name']}** - {row['price']}원")
            st.image(row['image_url'], width=120)
        with col2:
            qty = st.number_input(f"수량 ({row['name']})", min_value=0, step=1, key=row['name'])
        with col3:
            if qty > 0:
                st.session_state.cart[row['name']] = {
                    "price": row['price'],
                    "qty": qty
                }

    st.subheader("🧺 장바구니")
    total = sum(v["price"] * v["qty"] for v in st.session_state.cart.values())
    st.write(f"총 금액: **{total}원** / 예산 {st.session_state.budget}원")

    reason = st.text_area("이 구매를 선택한 이유를 작성하세요")

    if st.button("제출 → 결과 화면 이동"):
        st.session_state.reason = reason
        st.switch_page("app.py")

# --- RESULT SCREEN ---
def result_screen():
    st.title("📊 결과 화면")

    st.write("### 장바구니 내용")

    cart = st.session_state.cart
    total = sum(v["price"] * v["qty"] for v in cart.values())

    for name, data in cart.items():
        st.write(f"- {name}: {data['qty']}개 × {data['price']}원 = {data['qty'] * data['price']}원")

    st.write(f"### 총 금액: **{total}원**")
    st.write("### 작성 이유:")
    st.write(st.session_state.reason)

    st.write("---")
    st.write("결과 화면을 이미지로 저장하려면 브라우저 캡처 기능을 이용하세요.")

# --- PAGE LOGIC ---
if st.session_state.mission is None:
    start_screen()
elif st.session_state.reason is None:
    shopping_screen()
else:
    result_screen()


# requirements.txt
# Streamlit app dependencies
streamlit
pandas
