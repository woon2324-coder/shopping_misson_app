# app.py
import streamlit as st
import pandas as pd
import io
from PIL import Image

# ----------------------
# Helper: load products
# ----------------------
@st.cache_data
def load_products(path="products.csv"):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        # return an empty DataFrame with expected columns so app won't crash
        return pd.DataFrame(columns=["name", "price", "category", "image_url"]) 

# ----------------------
# App configuration
# ----------------------
st.set_page_config(page_title="Budget Mission App", layout="wide")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "start"  # start | shop | result
if "mission" not in st.session_state:
    st.session_state.mission = None
if "budget" not in st.session_state:
    st.session_state.budget = 0
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "reason" not in st.session_state:
    st.session_state.reason = ""

# ----------------------
# Start screen
# ----------------------
def start_screen():
    st.title("🎯 미션 선택하기")
    st.write("학생이 미션을 선택하고 예산을 할당받는 화면입니다.")

    missions = {
        "미션 1 - 기본": 10000,
        "미션 2 - 중간": 20000,
        "미션 3 - 챌린지": 30000,
    }

    mission = st.radio("미션 선택", list(missions.keys()))
    col1, col2 = st.columns([3,1])
    with col1:
        st.write("선택한 미션에 따라 예산이 자동으로 설정됩니다.")
    with col2:
        st.metric("예산", f"{missions[mission]}원")

    if st.button("선택 완료 — 쇼핑으로"):
        st.session_state.mission = mission
        st.session_state.budget = missions[mission]
        st.session_state.page = "shop"
        st.experimental_rerun()

# ----------------------
# Shopping screen
# ----------------------
def shopping_screen():
    st.title("🛒 쇼핑하기")
    st.write(f"현재 미션: **{st.session_state.mission}**  |  예산: **{st.session_state.budget}원**")

    df = load_products()

    if df.empty:
        st.warning("products.csv 파일을 찾을 수 없거나 비어 있습니다. 저장소에 products.csv 파일을 업로드했는지 확인하세요.

예시 컬럼: name,price,category,image_url")
        if st.button("예시 products.csv 만들기"):
            example = pd.DataFrame([
                {"name":"샌드위치","price":3000,"category":"음식","image_url":""},
                {"name":"물병","price":1000,"category":"잡화","image_url":""},
                {"name":"볼펜","price":500,"category":"학용품","image_url":""},
            ])
            example.to_csv("products.csv", index=False)
            st.success("products.csv 예시 파일을 생성했습니다. 페이지를 새로고침 해주세요.")
        return

    categories = list(df["category"].fillna("기타").unique())
    selected_category = st.selectbox("카테고리 선택", categories)
    filtered = df[df["category"] == selected_category]

    st.write("---")
    st.write("품목을 선택하고 수량을 입력하세요. 수량을 0으로 설정하면 장바구니에서 제거됩니다.")

    for idx, row in filtered.reset_index(drop=True).iterrows():
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.markdown(f"**{row['name']}** — {int(row['price'])}원")
            if pd.notna(row.get('image_url')) and row.get('image_url') != "":
                st.image(row['image_url'], width=120)
        with col2:
            # use a stable key that won't collide between different products
            key = f"qty_{idx}_{row['name']}"
            qty = st.number_input(f"수량 ({row['name']})", min_value=0, step=1, key=key)
        with col3:
            # show subtotal
            st.write(f"소계: {qty * int(row['price'])}원")

        # maintain cart in session_state
        if qty > 0:
            st.session_state.cart[row['name']] = {"price": int(row['price']), "qty": int(qty)}
        else:
            # remove item when qty is 0
            if row['name'] in st.session_state.cart:
                del st.session_state.cart[row['name']]

    st.write("---")
    st.subheader("🧺 장바구니")
    cart = st.session_state.cart
    if cart:
        total = sum(v['price'] * v['qty'] for v in cart.values())
        for name, data in cart.items():
            st.write(f"- {name}: {data['qty']}개 × {data['price']}원 = {data['qty'] * data['price']}원")
        st.write(f"**총 금액: {total}원** / 예산: {st.session_state.budget}원")
    else:
        # FIXED multi-line string
st.info("""1) 브라우저의 인쇄 기능(Ctrl+P 또는 Cmd+P)을 사용해 PDF로 저장하거나,
2) 운영체제의 화면 캡처 도구를 사용하세요.

또는 Streamlit에서 이미지로 직접 만들려면 서버사이드에서 PIL로 캡처 이미지를 생성하는 추가 코드가 필요합니다.
""")("장바구니가 비어 있습니다.")

    st.write("---")
    st.session_state.reason = st.text_area("이 구매를 선택한 이유를 작성하세요", value=st.session_state.reason)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("결과 보기 — 제출"):
            st.session_state.page = "result"
            st.experimental_rerun()
    with col2:
        if st.button("처음으로"):
            # reset and go to start
            st.session_state.page = "start"
            st.session_state.mission = None
            st.session_state.budget = 0
            st.session_state.cart = {}
            st.session_state.reason = ""
            st.experimental_rerun()

# ----------------------
# Result screen
# ----------------------
def result_screen():
    st.title("📊 결과 화면")

    cart = st.session_state.cart
    if not cart:
        st.warning("장바구니가 비어 있습니다. 쇼핑 화면으로 돌아가세요.")
        if st.button("쇼핑으로 돌아가기"):
            st.session_state.page = "shop"
            st.experimental_rerun()
        return

    total = sum(v['price'] * v['qty'] for v in cart.values())

    st.write("### 장바구니 내용")
    for name, data in cart.items():
        st.write(f"- {name}: {data['qty']}개 × {data['price']}원 = {data['qty'] * data['price']}원")

    st.write(f"### 총 금액: **{total}원**")
    st.write("### 작성한 이유:")
    st.write(st.session_state.reason)

    st.write("---")
    st.write("아래 버튼을 눌러 결과를 이미지(스크린샷)로 저장하는 방법을 안내합니다.")

    if st.button("결과 화면을 이미지로 저장하는 방법 보기"):
        st.info("1) 브라우저의 인쇄 기능(Ctrl+P 또는 Cmd+P)을 사용해 PDF로 저장하거나,
2) 운영체제의 화면 캡처 도구를 사용하세요.

또는 Streamlit에서 이미지로 직접 만들려면 서버사이드에서 PIL로 캡처 이미지를 생성하는 추가 코드가 필요합니다.")

    st.write("---")
    if st.button("처음으로 가기"):
        # reset all
        st.session_state.page = "start"
        st.session_state.mission = None
        st.session_state.budget = 0
        st.session_state.cart = {}
        st.session_state.reason = ""
        st.experimental_rerun()

# ----------------------
# Router
# ----------------------
if st.session_state.page == "start":
    start_screen()
elif st.session_state.page == "shop":
    shopping_screen()
elif st.session_state.page == "result":
    result_screen()
else:
    st.error("알 수 없는 페이지 상태입니다. 초기화합니다.")
    st.session_state.page = "start"
    st.experimental_rerun()


# requirements.txt (content should be in a separate file in your repo)
# streamlit
# pandas
# pillow
