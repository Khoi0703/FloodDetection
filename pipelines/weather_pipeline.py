from dagster import Definitions, define_asset_job, ScheduleDefinition
from assets.weather_assets import vietnam_geojson, province_coordinates, weather_forecasts

# Định nghĩa một Job
weather_job = define_asset_job(name="weather_job")

# Định nghĩa một Schedule (chạy mỗi 1 tiếng)
weather_schedule = ScheduleDefinition(
    job=weather_job,
    cron_schedule="0 * * * *",  # mỗi giờ
)

# Tập hợp các assets và schedules
defs = Definitions(
    assets=[vietnam_geojson, province_coordinates, weather_forecasts],
    jobs=[weather_job],
    schedules=[weather_schedule],
)
