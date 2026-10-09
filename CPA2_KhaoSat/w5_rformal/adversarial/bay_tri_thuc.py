"""
bay_tri_thuc.py — BỘ BẪY TRI THỨC: các mệnh đề học vụ phổ biến nhưng SAI.

Nguồn gốc: trong quá trình làm Tuần 5, tác giả nhận được HAI câu trả lời độc lập
cho cùng một câu hỏi ("TC nợ đọng tính thế nào?"), cả hai đều do trợ lý AI sinh ra,
trôi chảy và có vẻ hữu ích. Đối chiếu với văn bản gốc cho thấy chúng sai ở nhiều chỗ
kiểm chứng được — và **mâu thuẫn với nhau ở đúng công thức cốt lõi**.

Đây là bằng chứng trực tiếp cho giả thuyết H2 (*baseline có Coverage cao nhưng
Soundness thấp — tự tin một cách sai lầm*), thu được TRƯỚC khi chạy thí nghiệm
Tuần 21. Khác với bộ Adversarial dựa trên dữ liệu khuyết, nhóm này đánh vào chỗ
baseline **chắc chắn sẽ trả lời**, vì đây là thứ lặp đi lặp lại trên mạng.

Mỗi bản ghi có: mệnh đề bị bác, chân trị đúng, con trỏ nguồn, và cách kiểm lại.
Sinh ra: bay_tri_thuc.json (máy đọc) + BoBayTriThuc.md (người đọc).

Chạy: python3 bay_tri_thuc.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

MAU = {
    "M1": "Trợ lý AI #1 — trả lời câu hỏi 'cách xác định số tín chỉ nợ đọng'",
    "M2": "Trợ lý AI #2 — trả lời cùng câu hỏi, phiên bản khác",
}

BAY = [
    dict(
        id="B-01", mau=["M1", "M2"], nhom="nguong_dat",
        menh_de="Học phần được xem là đạt khi có điểm từ **5,0** trở lên (thang 10).",
        chan_tri="SAI (với học phần học tại ĐHCT)",
        dung="Học phần tích lũy được từ **điểm D**, mà bảng quy đổi đặt **D = 4,0–4,9**. "
             "Ngưỡng 5,0 là của QĐ5339 và theo QD-09 chỉ áp cho ĐIỂM CHUYỂN ĐỔI từ cơ sở "
             "đào tạo khác.",
        nguon="QĐ3266 Điều 22 khoản 3 và bảng ở khoản 2",
        hau_qua="Sinh viên có điểm 4,0–4,9 bị báo nhầm là chưa đạt; kéo theo sai tổng tín "
                "chỉ tích lũy, sai xếp trình độ năm học, sai cả kết luận cảnh báo học vụ.",
        kiem="ca C23c trong validate_rformal.py",
    ),
    dict(
        id="B-02", mau=["M1"], nhom="nguong_dat",
        menh_de="Học phần được xem là đạt khi có điểm chữ từ **C** trở lên.",
        chan_tri="SAI",
        dung="Ngưỡng là **D**, thấp hơn C ba bậc (D, D⁺, C). C tương ứng 5,5–6,4.",
        nguon="QĐ3266 Điều 22 khoản 3",
        hau_qua="Sai nặng hơn B-01: loại nhầm cả nhóm điểm 4,0–5,4.",
        kiem="bảng band/4 trong qd3266_r_formal_v1.lp",
    ),
    dict(
        id="B-03", mau=["M1"], nhom="con_so_bia",
        menh_de="Tổng số tín chỉ nợ không được vượt quá **150 %** khối lượng CTĐT thì mới "
                "được xét tốt nghiệp.",
        chan_tri="KHÔNG TỒN TẠI",
        dung="Chuỗi '150' không xuất hiện trong QĐ3266; trong QĐ5339 chỉ xuất hiện ở dải "
             "điểm Cambridge KET. Con số thật là **24 TC**, và nó là ngưỡng **cảnh báo học "
             "tập**, không phải điều kiện xét tốt nghiệp.",
        nguon="QĐ3266 Điều 18 khoản 2 điểm c (đã tìm toàn văn cả hai văn bản)",
        hau_qua="Gán một điều kiện tốt nghiệp không tồn tại; đồng thời giấu mất ngưỡng "
                "cảnh báo thật.",
        kiem="ca C30/C31 (biên 24/25 TC)",
    ),
    dict(
        id="B-04", mau=["M2"], nhom="con_so_bia",
        menh_de="Nợ quá nhiều tín chỉ (**trên 15–20 TC tùy quy định từng khoa**) thì bị "
                "**đình chỉ học tập**.",
        chan_tri="SAI ba lần trong một câu",
        dung="(1) Sai HỆ QUẢ: nợ tín chỉ dẫn tới **cảnh báo học tập**, không phải đình chỉ. "
             "Đình chỉ 1 HK chỉ xảy ra khi bị kỷ luật ở mức đó, hoặc ĐRL yếu/kém 2 HK liên "
             "tiếp. (2) Sai CON SỐ: ngưỡng là **24 TC**. (3) Sai THẨM QUYỀN: ngưỡng do quy "
             "chế cấp Trường đặt, không 'tùy từng khoa'.",
        nguon="QĐ3266 Điều 18 khoản 2 điểm c (cảnh báo) và khoản 3 (đình chỉ)",
        hau_qua="Doạ sinh viên bằng một hậu quả nặng hơn thực tế, dựa trên con số bịa.",
        kiem="ca C31 và mục 10 của qd3266_r_formal_v1.lp",
    ),
    dict(
        id="B-05", mau=["M1", "M2"], nhom="ky_hieu",
        menh_de="Học phần có **dấu (*)** là học phần **bắt buộc**.",
        chan_tri="SAI — gần như ngược lại",
        dung="Dấu (*) CÓ tồn tại trong CTĐT, nhưng chú thích cuối bảng ghi: *'(*) là học phần "
             "**điều kiện**, không tính điểm trung bình chung tích lũy. Sinh viên có thể hoàn "
             "thành bằng hình thức nộp chứng chỉ ... hoặc học tích lũy.'* Tức nó đánh dấu đúng "
             "nhóm học phần **không** vào ĐTBCTL và **có thể miễn bằng chứng chỉ**.",
        nguon="CTĐT CNTT K49 (QĐ 2423/QĐ-ĐHCT 05/6/2023), chú thích cuối bảng trang 4; "
              "khớp với QĐ3266 Điều 7 khoản 6",
        hau_qua="Hiểu ngược ý nghĩa ký hiệu; dẫn tới tính nhầm ĐTBCTL và bỏ lỡ quyền xin "
                "miễn bằng chứng chỉ.",
        kiem="ctdt_cntt_k49.lp — danh_dau_sao_la(hoc_phan_dieu_kien)",
        tu_phe="Ở lần đối chiếu đầu tác giả kết luận 'dấu (*) không xuất hiện ở cả hai văn "
                "bản' — đúng với hai QĐ nhưng SAI vì chưa tra CTĐT. Ghi lại để nhớ: phạm vi "
                "tìm kiếm hẹp cũng sinh ra kết luận âm tính sai.",
    ),
    dict(
        id="B-06", mau=["M2"], nhom="con_so_bia",
        menh_de="Tổng số tín chỉ của ngành **thường từ 135–150 TC**.",
        chan_tri="SAI với ngành đang xét",
        dung="CTĐT CNTT K49: **161 TC** (bắt buộc 125, tự chọn 36) — nằm ngoài khoảng được "
             "nêu. Quy chế KHÔNG quy định con số này; nó thuộc từng CTĐT.",
        nguon="CTĐT CNTT K49, bảng tổng trang 4: 'Tổng cộng: 161 TC (Bắt buộc: 125 TC; "
              "Tự chọn: 36 TC)'",
        hau_qua="Sai tổng tín chỉ đích → sai mọi phép tính 'còn thiếu bao nhiêu tín chỉ'.",
        kiem="ctdt_cntt_k49.lp — tc_toi_thieu_ctdt(161) và ràng buộc cộng ba khối",
    ),
    dict(
        id="B-07", mau=["M1", "M2"], nhom="mau_thuan_noi_bo",
        menh_de="Hai mẫu đưa ra HAI công thức khác nhau cho cùng một đại lượng: "
                "M1 — *TC nợ = TC đã đăng ký − TC đã đạt*; "
                "M2 — *TC nợ = Tổng TC ngành − TC đã đạt*.",
        chan_tri="MÂU THUẪN; công thức của M2 dẫn tới kết luận vô lý",
        dung="Quy chế không định nghĩa thuật ngữ này (xem QD-03). Nhưng công thức của M2 bị "
             "bác bằng phản chứng: với CTĐT 161 TC và ngưỡng cảnh báo 24 TC, sinh viên phải "
             "tích lũy **≥ 137 TC** mới thoát cảnh báo. Nghĩa là **gần như toàn bộ sinh viên "
             "chưa tới năm cuối đều bị cảnh báo học tập** — một hệ quả không thể đúng. "
             "M2 còn tự mâu thuẫn: ngay sau công thức đó lại viết 'hoặc đơn giản hơn: cộng "
             "tổng TC các học phần bị trượt/chưa học', vốn là một đại lượng khác hẳn.",
        nguon="Phản chứng dùng số thật của CTĐT CNTT K49 (161 TC) và QĐ3266 Điều 18 k.2 đ.c "
              "(24 TC)",
        hau_qua="Nếu cài theo M2, hệ thống sẽ cảnh báo học vụ gần như mọi sinh viên.",
        kiem="ca C27–C29 (định nghĩa đang dùng) và phản chứng trong BoBayTriThuc.md mục 3",
    ),
    dict(
        id="B-08", mau=["M2"], nhom="dung",
        menh_de="Một năm học tại ĐHCT có **3 học kỳ**.",
        chan_tri="ĐÚNG",
        dung="QĐ3266 Điều 6 khoản 1: 'Mỗi năm học được tổ chức thành 03 HK gọi là Học kỳ 1, "
             "Học kỳ 2 và Học kỳ 3.'",
        nguon="QĐ3266 Điều 6 khoản 1",
        hau_qua="—",
        kiem="đưa vào bộ để bộ không toàn ca sai: một bộ đối kháng chỉ chứa mệnh đề sai sẽ "
              "thưởng cho hệ thống nào luôn trả lời 'sai'.",
    ),
]


def main():
    HERE.mkdir(exist_ok=True)
    (HERE / "bay_tri_thuc.json").write_text(
        json.dumps({"mau": MAU, "bay": BAY}, ensure_ascii=False, indent=2), encoding="utf-8")

    sai = [b for b in BAY if b["nhom"] != "dung"]
    L = ["# BỘ BẪY TRI THỨC — mệnh đề học vụ phổ biến nhưng sai\n",
         "**Sinh tự động** từ `bay_tri_thuc.py`. Dành cho bộ Adversarial của Tuần 17 và cho "
         "phần bàn luận về giả thuyết **H2**.\n",
         "## 1. Bộ này đến từ đâu\n",
         "Trong lúc làm Tuần 5, tác giả nhận được **hai câu trả lời độc lập** cho cùng một câu "
         "hỏi — *\"TC nợ đọng tính thế nào?\"* — cả hai do trợ lý AI sinh ra. Cả hai đều trôi "
         "chảy, có cấu trúc, có hướng dẫn thao tác cụ thể, và **không câu nào kèm cảnh báo về "
         "độ chắc chắn**. Đối chiếu với văn bản gốc: "
         f"**{len(sai)} mệnh đề sai** trên tổng {len(BAY)} mệnh đề kiểm được.\n",
         "Điều đáng giá nhất không phải số lỗi, mà là **hai câu trả lời mâu thuẫn với nhau ở "
         "đúng công thức cốt lõi** (B-07). Một người đọc chỉ nhận một trong hai sẽ không có "
         "cách nào biết điều đó.\n",
         "> Đây là **bằng chứng cho H2 thu được trước thí nghiệm**, và là loại ca đối kháng "
         "khác với nhóm dữ liệu khuyết: ở đây baseline **chắc chắn sẽ trả lời**, vì mệnh đề "
         "sai chính là thứ lặp đi lặp lại trên mạng.\n",
         "## 2. Bảng bẫy\n",
         "| Mã | Nhóm | Mệnh đề | Chân trị | Nguồn đối chiếu |", "|---|---|---|---|---|"]
    ten_nhom = {"nguong_dat": "ngưỡng đạt", "con_so_bia": "con số bịa",
                "ky_hieu": "hiểu sai ký hiệu", "mau_thuan_noi_bo": "mâu thuẫn nội bộ",
                "dung": "đúng (ca đối chứng)"}
    for b in BAY:
        md = b["menh_de"].replace("\n", " ")
        md = (md[:90] + "…") if len(md) > 90 else md
        L.append(f"| **{b['id']}** | {ten_nhom[b['nhom']]} | {md} | {b['chan_tri']} | {b['nguon']} |")

    L.append("\n## 3. Chi tiết\n")
    for b in BAY:
        L.append(f"### {b['id']} — {b['chan_tri']}\n")
        L.append(f"**Mệnh đề:** {b['menh_de']}\n")
        L.append(f"**Đúng ra là:** {b['dung']}\n")
        L.append(f"**Nguồn:** {b['nguon']}\n")
        if b["hau_qua"] != "—":
            L.append(f"**Hậu quả nếu tin theo:** {b['hau_qua']}\n")
        L.append(f"**Kiểm lại ở:** {b['kiem']}\n")
        L.append(f"**Xuất hiện ở:** {', '.join(MAU[m].split('—')[0].strip() for m in b['mau'])}\n")
        if b.get("tu_phe"):
            L.append(f"> **Tự phê:** {b['tu_phe']}\n")
        L.append("")

    L.append("## 4. Cách dùng ở Tuần 17 và Tuần 21\n")
    L.append("- Mỗi bẫy thành **một câu hỏi Q-Real** đặt thẳng vào mệnh đề sai "
             "(*\"Em được 4,5 điểm môn CT177, vậy có đạt không?\"*).")
    L.append("- Ground truth là cột *Đúng ra là* kèm con trỏ điều khoản — chấm được tự động.")
    L.append("- Đo trên baseline: kỳ vọng **Coverage ≈ 100 %, Soundness thấp** — đúng dạng H2 "
             "dự đoán. CPA² phải hoặc trả lời đúng kèm chứng chỉ, hoặc từ chối; **không được "
             "trả lời sai**.")
    L.append("- B-08 là **ca đối chứng dương**: một bộ chỉ gồm mệnh đề sai sẽ thưởng cho hệ "
             "thống nào luôn bác bỏ. Cần thêm ca đúng để phát hiện kiểu gian lận đó.\n")
    L.append("## 5. Hạn chế của bộ này\n")
    L.append("- Cỡ mẫu rất nhỏ (2 câu trả lời, 8 mệnh đề) và **không lấy mẫu ngẫu nhiên** — "
             "đây là ca thuận tiện, không phải khảo sát. Không được suy ra tỷ lệ lỗi của bất "
             "kỳ mô hình nào từ đây.")
    L.append("- Không ghi lại mô hình nào sinh ra câu trả lời, ngày nào, prompt gì. Nếu muốn "
             "dùng như dữ liệu chính thức trong luận văn thì **phải chạy lại có kiểm soát**: "
             "cố định mô hình, prompt, ngày, và lưu nguyên văn.")
    L.append("- Giá trị hiện tại của bộ này là **định tính**: nó cho thấy dạng lỗi tồn tại và "
             "đáng đo, chứ chưa đo được tần suất.\n")

    (HERE / "BoBayTriThuc.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Đã ghi bay_tri_thuc.json và BoBayTriThuc.md — {len(BAY)} mệnh đề "
          f"({len(sai)} sai, {len(BAY)-len(sai)} đúng làm đối chứng).")


if __name__ == "__main__":
    main()
