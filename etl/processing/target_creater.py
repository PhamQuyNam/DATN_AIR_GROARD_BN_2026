import pandas as pd
import pathlib
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_target_features(df: pd.DataFrame, horizon: int = 6) -> pd.DataFrame:
    """
    Tạo biến Target: AQI tại thời điểm (t + horizon).
    Mặc định horizon = 6 giờ theo yêu cầu của đồ án.
    """
    df = df.copy()

    # 1. Đảm bảo dữ liệu được sắp xếp theo làng và thời gian
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(['village', 'timestamp']).reset_index(drop=True)

    # 2. TẠO TARGET (LEAD FEATURE)
    # Chúng ta dịch chuyển cột aqi_current ngược lên 6 bước (shift -6)
    # Nghĩa là tại dòng của 10:00 sáng, target sẽ là giá trị AQI của lúc 16:00 chiều
    logger.info(f"Đang tạo target aqi_{horizon}h bằng cách dịch chuyển ngược (Lead)...")

    df[f'target_aqi_{horizon}h'] = df.groupby('village')['aqi_current'].shift(-horizon)

    # 3. LOẠI BỎ CÁC DÒNG CUỐI CÙNG CỦA MỖI LÀNG
    # Vì 6 giờ cuối cùng của dữ liệu sẽ không có "tương lai" để gán vào target
    before_len = len(df)
    df = df.dropna(subset=[f'target_aqi_{horizon}h'])

    logger.info(f"Đã loại bỏ {before_len - len(df)} dòng không có dữ liệu tương lai (6h cuối của mỗi làng).")

    return df


def main():
    # Input lấy từ file đã CLEANED (dataset_ready_for_ml.csv)
    input_path = pathlib.Path(
        r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\data\processed\dataset_ready_for_ml.csv")
    output_dir = pathlib.Path(r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\data\finally")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"❌ Không tìm thấy file đã clean tại: {input_path}")
        return

    # Đọc dữ liệu
    df = pd.read_csv(input_path)

    # Tạo Target
    df_final = create_target_features(df, horizon=6)

    # Lưu file cuối cùng - Đây là file dùng để TRAIN MODEL
    output_file = output_dir / "final_dataset_target_6h.csv"
    df_final.to_csv(output_file, index=False, encoding="utf-8-sig")

    logger.info(f"✅ ĐÃ HOÀN THÀNH BỘ DỮ LIỆU CUỐI CÙNG!")
    logger.info(f"📊 Kích thước Dataset Finally: {df_final.shape}")
    logger.info(f"🚀 Đường dẫn: {output_file}")


if __name__ == "__main__":
    main()