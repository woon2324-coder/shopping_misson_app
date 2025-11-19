# app.py


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
