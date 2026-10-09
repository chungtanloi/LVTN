%%=============================================================================
%% ĐÃ THAY THẾ Ở TUẦN 6 — file này chỉ còn giá trị lịch sử, validate_rformal.py
%% không còn nạp nó. Dùng ../w6_curriculum/curriculum_cntt_k49.lp (sinh tự động,
%% đủ 78 dòng) + curriculum_schema.lp.
%% LỖI ĐÃ BIẾT của bản này (phát hiện khi chép lại đủ khung CTĐT ở Tuần 6):
%%   · Nhóm "tự chọn tự do 15 TC" bỏ sót CT550E (LVTN 15 TC) và CT501E (TLTN 6 TC):
%%     trong CTĐT, hai học phần này nằm CÙNG ô gộp "15" với 7 học phần 3 TC.
%%     Sinh viên làm luận văn sẽ bị kết luận thiếu nhóm tự chọn.
%%   · nhieu_hon_mot_cn coi việc học hai cặp chuyên ngành là vi phạm; CTĐT không cấm,
%%     chỉ tính một cặp cho nhóm (CQ-04).
%%   · Chưa mã hoá 15 TC tự chọn khối đại cương.
%%=============================================================================
%%=============================================================================
%% ctdt_cntt_k49.lp — THAM SỐ THẬT của CTĐT ngành Công nghệ thông tin, Khoá 49
%%
%% Nguồn: Chương trình đào tạo trình độ đại học ngành Công nghệ thông tin
%%        (mã ngành 7480201), ban hành theo QĐ 2423/QĐ-ĐHCT ngày 05/6/2023.
%%        File: LVTN/NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf
%%        Bảng tổng ở trang 4 — đối chiếu trực tiếp trên ảnh (trang 4 không có
%%        lớp văn bản, pdftotext chỉ lấy được 3 trang đầu).
%%
%% VÌ SAO FILE NÀY TÁCH RIÊNG: các con số dưới đây KHÔNG do quy chế quy định.
%% QĐ3266 Điều 32 chỉ nói "tích lũy đủ các học phần và số TC quy định trong CTĐT"
%% — con số cụ thể nằm ở đây và thay đổi theo (ngành, khoá). Trộn chúng vào file
%% quy tắc quy chế là cách chắc chắn nhất để KB sai khi đổi ngành hoặc đổi khoá.
%%=============================================================================

ctdt(cntt_k49).
nganh_ma("7480201").
danh_hieu(ky_su).

%% --- Thời gian đào tạo -------------------------------------------------------
%% "Thời gian đào tạo: 4.5 năm"  → theo QĐ3266 Điều 5: tối đa 9 năm (18 nửa năm).
thiet_ke_nam2(9).                 % 4,5 năm = 9 nửa năm
khoa_tu_k45. khoa_tu_k47. khoa_den_k49.

%% --- Khối lượng: Tổng cộng 161 TC (Bắt buộc 125 TC; Tự chọn 36 TC) -----------
tc_toi_thieu_ctdt(161).
tc_bat_buoc_ctdt(125).
tc_tu_chon_ctdt(36).

khoi(dai_cuong,    56, 41, 15).   % (khối, tổng, bắt buộc, tự chọn)
khoi(co_so_nganh,  46, 46,  0).
khoi(chuyen_nganh, 59, 38, 21).

%% kiểm tra nội tại: ba khối phải cộng đúng bằng tổng
:- tc_toi_thieu_ctdt(T), T != #sum{ S,K : khoi(K,S,_,_) }.
:- tc_bat_buoc_ctdt(B), B != #sum{ S,K : khoi(K,_,S,_) }.
:- tc_tu_chon_ctdt(C), C != #sum{ S,K : khoi(K,_,_,S) }.

%% --- Học phần cuối khoá ------------------------------------------------------
%% Ba hình thức của QĐ3266 Điều 31 hiện hình bằng ba học phần khác nhau.
%% LƯU Ý: prototype Tuần 4 dùng "CT466E = Luận văn tốt nghiệp, 10 TC" — SAI cả ba
%% chi tiết. CT466E là NIÊN LUẬN 3 TC; luận văn tốt nghiệp là CT550E 15 TC.
course("CT466E",  3). ten("CT466E", "Niên luận - CNTT").
course("CT550E", 15). ten("CT550E", "Luận văn tốt nghiệp - CNTT").
course("CT501E",  6). ten("CT501E", "Tiểu luận tốt nghiệp - CNTT").
course("CT518E",  5). ten("CT518E", "Thực tập doanh nghiệp - CNTT").

hinh_thuc_cuoi_khoa("CT550E", luan_van).
hinh_thuc_cuoi_khoa("CT501E", tieu_luan).

%% --- TIÊN QUYẾT THEO TÍN CHỈ TÍCH LŨY (loại T4b — MỚI, chưa có trong Tuần 2) --
%% Taxonomy Tuần 2 chỉ mô hình hoá tiên quyết học phần → học phần. CTĐT thật còn
%% có tiên quyết dạng NGƯỠNG TÍN CHỈ, biểu diễn trong bảng là "≥80TC", "≥120TC".
tien_quyet_tc("CT466E",  80).
tien_quyet_tc("CT550E", 120).
tien_quyet_tc("CT501E", 120).
tien_quyet_tc("CT518E", 125).

du_dk_tc(C)  :- tien_quyet_tc(C,N), tc_tich_luy(T), T >= N.
thieu_tc(C,D) :- tien_quyet_tc(C,N), tc_tich_luy(T), T < N, D = N - T.

%% Trả lời được một phần câu hỏi mà QĐ3266 Điều 31 để ngỏ ("điều kiện do đơn vị
%% đào tạo quy định"): ngưỡng tín chỉ thì CTĐT có nói. Các điều kiện khác của
%% đơn vị đào tạo vẫn nằm ngoài — nên kết luận chỉ ở mức "đủ điều kiện về tín chỉ".
du_dk_tin_chi_lam_lvtn :- du_dk_tc("CT550E").

%% --- Học kỳ tổ chức ----------------------------------------------------------
%% CT518E chỉ mở ở HK III — ràng buộc xếp kỳ, dùng cho nhánh lập kế hoạch (RQ3).
chi_mo_hk("CT518E", 3).

%% --- Nhóm tự chọn chuyên ngành: CN1 / CN2 / CN3 ------------------------------
%% Cấu trúc thật KHÁC hẳn "10 chọn 2" mà Tuần 2 và prototype Tuần 4 giả định:
%% phải chọn 6 TC từ ĐÚNG MỘT trong ba cặp chuyên ngành.
cap_cn(cn1, "CT211", "CT297").    % An ninh mạng      / Pháp y máy tính
cap_cn(cn2, "CT449", "CT484").    % Phát triển web    / Phát triển di động
cap_cn(cn3, "CT522", "CT279").    % IoT               / Blockchain
tc_nhom_cn(6).

chon_cn(G) :- cap_cn(G,A,B), passed(A), passed(B).
dat_nhom_cn :- chon_cn(_).
%% ràng buộc phân hoạch: không được lấy hai cặp khác nhau để tính cùng một lúc
nhieu_hon_mot_cn :- chon_cn(G1), chon_cn(G2), G1 != G2.

%% --- Nhóm tự chọn tự do 15 TC ------------------------------------------------
tu_chon_tu_do("CT478"). tu_chon_tu_do("CT283"). tu_chon_tu_do("CT233").
tu_chon_tu_do("CT482"). tu_chon_tu_do("CT210"). tu_chon_tu_do("CT219").
tu_chon_tu_do("CT312").
tc_tu_chon_tu_do(15).

tc_tu_chon_dat(X) :- X = #sum{ CR,C : tu_chon_tu_do(C), passed(C), course(C,CR) }.
dat_tu_chon_tu_do :- tc_tu_chon_dat(X), tc_tu_chon_tu_do(M), X >= M.

%% --- Học phần điều kiện: dấu (*) trong CTĐT ----------------------------------
%% Chú thích cuối bảng CTĐT: "(*): là học phần ĐIỀU KIỆN, không tính điểm trung
%% bình chung tích lũy. Sinh viên có thể hoàn thành các học phần trên bằng hình
%% thức nộp chứng chỉ theo quy định của Trường ĐHCT hoặc học tích lũy."
%% → dấu (*) KHÔNG có nghĩa "bắt buộc"; nó đánh dấu đúng nhóm học phần mà
%%   QĐ3266 Điều 7 khoản 6 gọi là học phần điều kiện.
danh_dau_sao_la(hoc_phan_dieu_kien).
