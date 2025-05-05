import streamlit as st
from streamlit_folium import st_folium
from utils.map_utils import create_map
from dagster import DagsterInstance, Definitions, define_asset_job, materialize
import pandas as pd
import ast  # Để xử lý chuỗi nếu cần

st.title("📍 Bản đồ dự báo thời tiết Việt Nam")

# Load all required assets
from assets.weather_assets import vietnam_geojson, weather_forecasts, province_coordinates

# Create job definition and execute assets
defs = Definitions(assets=[vietnam_geojson, province_coordinates, weather_forecasts])
instance = DagsterInstance.get()
result = materialize(
    [vietnam_geojson, province_coordinates, weather_forecasts],
    instance=instance,
)

# Get materialized values
geojson_data = result.output_for_node("vietnam_geojson")
weather_data = result.output_for_node("weather_forecasts")

# Đặt ngưỡng lượng mưa cao
RAIN_THRESHOLD = 50 # mm trong 5 ngày

# Tạo bản đồ với dữ liệu thời tiết
map_object = create_map(geojson_data, weather_data, rain_threshold=RAIN_THRESHOLD)
st_data = st_folium(map_object, width=700, height=500)

# Hiển thị cảnh báo các khu vực có lượng mưa cao
high_rain_provinces = [
    province for province, data in weather_data.items()
    if data["total_rain"] > RAIN_THRESHOLD
]

if high_rain_provinces:
    st.warning("⚠️ **Cảnh báo các khu vực có lượng mưa cao:**")
    for province in high_rain_provinces:
        st.markdown(f"- **{province}**: {weather_data[province]['total_rain']} mm")
else:
    st.success("✅ Không có khu vực nào vượt ngưỡng lượng mưa cao.")

if "selected_province" not in st.session_state:
    st.session_state.selected_province = None

if st_data:
    if "last_active_drawing" in st_data and st_data["last_active_drawing"]:
        properties = st_data["last_active_drawing"]["properties"]
        province_name = properties.get("ten_tinh", None)
        if province_name:
            st.session_state.selected_province = province_name

selected_province = st.selectbox(
    "🔍 Chọn tỉnh/thành phố:",
    [feature["properties"]["ten_tinh"] for feature in geojson_data["features"]],
    index=[feature["properties"]["ten_tinh"] for feature in geojson_data["features"]].index(st.session_state.selected_province)
    if st.session_state.selected_province else 0
)

if selected_province != st.session_state.selected_province:
    st.session_state.selected_province = selected_province

if st.button("📡 Xem dự báo thời tiết"):
    if st.session_state.selected_province in weather_data:
        province_weather = weather_data[st.session_state.selected_province]
        with st.expander(f"📍 Dự báo thời tiết tại {st.session_state.selected_province}", expanded=True):
            st.subheader("📅 **Dự báo thời tiết 5 ngày**")
            st.dataframe(province_weather["forecast"])
            st.markdown(f"### 🌧️ **Tổng lượng mưa trong 5 ngày**: `{province_weather['total_rain']} mm`")
            st.info("ℹ️ Dữ liệu có thể được lấy từ cache để tối ưu hóa.")
    else:
        st.error("❌ Không có dữ liệu thời tiết cho tỉnh/thành phố này!")

# Đường dẫn file CSV
CSV_FILE = "weather_data.csv"

# Chuyển đổi dữ liệu thời tiết thành DataFrame
def save_weather_data_to_csv(weather_data, csv_file):
    data = []
    for province, info in weather_data.items():
        # Kiểm tra xem "forecast" có tồn tại
        if "forecast" in info:
            forecast = info["forecast"]

            # Nếu forecast là chuỗi, chuyển đổi về DataFrame
            if isinstance(forecast, str):
                try:
                    # Chuyển chuỗi về DataFrame
                    forecast_df = pd.read_csv(pd.compat.StringIO(forecast))
                except Exception as e:
                    st.warning(f"Lỗi khi chuyển đổi forecast cho tỉnh/thành phố {province}: {e}")
                    continue
            elif isinstance(forecast, pd.DataFrame):
                forecast_df = forecast
            else:
                st.warning(f"Dữ liệu forecast không hợp lệ cho tỉnh/thành phố: {province}")
                continue

            # Trích xuất dữ liệu từ DataFrame
            for _, row in forecast_df.iterrows():
                data.append({
                    "Tỉnh/Thành phố": province,
                    "Ngày": row.get("📅 Ngày", "N/A"),
                    "Nhiệt độ trung bình (°C)": row.get("🌡️ Nhiệt độ trung bình (°C)", "N/A"),
                    "Độ ẩm trung bình (%)": row.get("💧 Độ ẩm trung bình (%)", "N/A"),
                    "Gió trung bình (m/s)": row.get("🌬️ Gió trung bình (m/s)", "N/A"),
                    "Tổng lượng mưa (mm)": row.get("🌧️ Tổng lượng mưa (mm)", "N/A")
                })
        else:
            st.warning(f"Dữ liệu không hợp lệ cho tỉnh/thành phố: {province}")
    
    # Tạo DataFrame và lưu vào CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        st.success(f"Dữ liệu thời tiết đã được lưu vào file `{csv_file}`")
    else:
        st.error("Không có dữ liệu hợp lệ để lưu vào CSV.")

# Gọi hàm lưu dữ liệu sau khi xử lý xong
save_weather_data_to_csv(weather_data, CSV_FILE)

# # Hiển thị dữ liệu thời tiết
# st.write(weather_data)
