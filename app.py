# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ----------------------
# Config & helpers
# ----------------------
st.set_page_config(page_title="Budget Mission App", layout="wide")

@st.cache_data
def load_products(path="products.csv"):
    """Load products.csv and ensure expected columns and types."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame(columns=["name", "price", "category", "image_url"])

    # normalize columns
    expected = ["name", "price", "category", "image_url"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    # coerce price to int (safe)
    def _parse_price(x):
        try:
            return int(float(x))
        except Exception:
            return 0

    df["price"] = df["price"].apply(_parse_price)
    df["category"] = df["category"].fillna("기타")

    return df[expected]


def generate_result_image(cart, reason, total, budget):
    """Generate a simple PNG image summarizing the cart and reason using PIL."""
    # canvas size depends on content length — we'll calculate a reasonable size
    lines = []
    lines.append(f"미션 예산: {budget}원")
    lines.append("")
    lines.append("장바구니:")
    for name, data in cart.items():
        lines.append(f"- {name}: {data['qty']} x {data['price']}원 = {data['qty']*data['price']}원")
    lines.append("")
    lines.append(f"총 금액: {total}원")
    lines.append("")
    lines.append("선택 이유:")

    # wrap reason into multiple lines
    if reason:
        # naive wrap at 40 chars
        import textwrap
        wrapped = textwrap.wrap(reason, width=40)
        lines.extend(wrapped)
    else:
        lines.append("(작성된 이유가 없습니다)")

    # estimate image height
    line_height = 24
    padding = 20
    width = 900
    height = padding * 2 + line_height * (len(lines) + 1)

    img = Image.new("RGB", (width, max(240, height)), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # load a default truetype font if available
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    y = padding
    for line in lines:
        draw.text((padding, y), line, fill=(0, 0, 0), font=font)
        y += line_height

    # return bytes
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


# ----------------------
# Session state init
# ----------------------
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
# Screens
# ----------------------

def start_screen():
    st.title("🎯 미션 선택하기")
    st.write("학생이 미션을 선택하고 예산을 할당받는 화면입니다.")

    missions = {
        "미션 1 - 기본": 10000,
        "미션 2 - 중간": 20000,
        "미션 3 - 챌린지": 30000,
    }

    # show choices and preview budget
    cols = st.columns([2, 1])
    with cols[0]:
        mission = st.radio("미션 선택", list(missions.keys()))
    with cols[1]:
        st.metric("예산(미리보기)", f"{missions.get(st.session_state.get('mission', mission))}원")

    if st.button("선택 완료 — 쇼핑으로"):
        # set session values and go to shop
        st.session_state.mission = mission
        st.session_state.budget = missions[mission]
        st.session_state.page = "shop"
        st.rerun()


def shopping_screen():
    st.title("🛒 쇼핑하기")
    st.write(f"현재 미션: **{st.session_state.mission}**  |  예산: **{st.session_state.budget}원**")

    df = load_products()

    if df.empty:
        st.warning("""products.csv 파일이 없거나 비어 있습니다. 리포지토리에 products.csv를 업로드했는지 확인하세요.

예시 컬럼: name,price,category,image_url""")
        if st.button("예시 products.csv 만들기"):
            example = pd.DataFrame([
                {"name":"샌드위치","price":3000,"category":"음식","image_url":""},
                {"name":"물병","price":1000,"category":"잡화","image_url":""},
                {"name":"볼펜","price":500,"category":"학용품","image_url":""},
            ])
            example.to_csv("products.csv", index=False)
            st.success("products.csv 예시 파일을 생성했습니다. 페이지를 새로고침하세요.")
        return

    categories = list(df["category"].unique())
    selected_category = st.selectbox("카테고리 선택", categories)
    filtered = df[df["category"] == selected_category].reset_index(drop=True)

    st.write("---")
    st.write("품목을 선택하고 수량을 입력하세요. 수량을 0으로 설정하면 장바구니에서 제거됩니다.")

    # show product entries
    for idx, row in filtered.iterrows():
        name = str(row["name"]) if pd.notna(row["name"]) else f"상품_{idx}"
        price = int(row["price"]) if pd.notna(row["price"]) else 0
        image_url = row.get("image_url", "")

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{name}** — {price}원")
            if image_url:
                try:
                    st.image(image_url, width=120)
                except Exception:
                    st.write("(이미지를 불러올 수 없습니다)")
        with col2:
            key = f"qty_{selected_category}_{idx}"
            qty = st.number_input(f"수량 ({name})", min_value=0, step=1, value=st.session_state.get('cart', {}).get(name, {}).get('qty', 0), key=key)
        with col3:
            st.write(f"소계: {qty * price}원")

        # update cart
        if qty > 0:
            st.session_state.cart[name] = {"price": price, "qty": qty}
        else:
            if name in st.session_state.cart:
                del st.session_state.cart[name]

    st.write("---")
    st.subheader("🧺 장바구니")
    cart = st.session_state.cart
    if cart:
        total = sum(v['price'] * v['qty'] for v in cart.values())
        for name, data in cart.items():
            st.write(f"- {name}: {data['qty']}개 × {data['price']}원 = {data['qty'] * data['price']}원")
        st.write(f"**총 금액: {total}원** / 예산: {st.session_state.budget}원")
    else:
        st.info("장바구니가 비어 있습니다.")

    st.write("---")
    st.session_state.reason = st.text_area("이 구매를 선택한 이유를 작성하세요", value=st.session_state.reason)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("결과 보기 — 제출"):
            st.session_state.page = "result"
            st.rerun()
    with col2:
        if st.button("처음으로"):
            st.session_state.page = "start"
            st.session_state.mission = None
            st.session_state.budget = 0
            st.session_state.cart = {}
            st.session_state.reason = ""
            st.rerun()


def result_screen():
    st.title("📊 결과 화면")

    cart = st.session_state.cart
    if not cart:
        st.warning("장바구니가 비어 있습니다. 쇼핑 화면으로 돌아가세요.")
        if st.button("쇼핑으로 돌아가기"):
            st.session_state.page = "shop"
            st.rerun()
        return

    total = sum(v['price'] * v['qty'] for v in cart.values())

    st.write("### 장바구니 내용")
    for name, data in cart.items():
        st.write(f"- {name}: {data['qty']}개 × {data['price']}원 = {data['qty'] * data['price']}원")

    st.write(f"### 총 금액: **{total}원**")
    st.write("### 작성한 이유:")
    st.write(st.session_state.reason)

    st.write("---")
    st.write("결과를 이미지로 다운로드할 수 있습니다.")

    # generate and provide PNG
    try:
        bio = generate_result_image(cart, st.session_state.reason, total, st.session_state.budget)
        st.download_button("결과 이미지 다운로드(PNG)", data=bio, file_name="result.png", mime="image/png")
    except Exception as e:
        st.error(f"이미지 생성 중 오류가 발생했습니다: {e}")
        st.info("대안: 브라우저의 인쇄(Ctrl+P / Cmd+P)로 PDF로 저장하거나 스크린샷을 이용하세요.")

    st.write("---")
    if st.button("처음으로 가기"):
        st.session_state.page = "start"
        st.session_state.mission = None
        st.session_state.budget = 0
        st.session_state.cart = {}
        st.session_state.reason = ""
        st.rerun()


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
    st.rerun()


# requirements.txt
# streamlit
# pandas
# pillow
