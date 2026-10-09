%%=============================================================================
%% qd5339_r_formal_v1.lp — R-Formal v1.1, nhóm M
%% Hình thức hoá QĐ 5339/QĐ-ĐHCT (05/11/2019) — Quy định xét miễn và công nhận
%% điểm học phần trong CTĐT trình độ đại học hệ chính quy.
%%
%% Văn bản này là ĐÍCH của con trỏ tại QĐ3266 Điều 5 (bản ghi R-H03) và là nguồn
%% duy nhất của toàn bộ loại T5 (Exemption) trong taxonomy Tuần 2.
%%
%% NẠP CÙNG qd3266_r_formal_v1.lp — hai file dùng chung vị từ course/2, g10/2,
%% g4/2, passed/1, hp_dieu_kien/1, khong_tinh_tb/1.
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 0. CON TRỎ NGUỒN  (lược đồ v1.1: rule_src/5, có mã văn bản)
%% ---------------------------------------------------------------------------
rule_src(r_m02,  qd5339, 3, 2,  none).
rule_src(r_m03a, qd5339, 3, 2,  none).
rule_src(r_m03b, qd5339, 3, 2,  none).
rule_src(r_m04,  qd5339, 3, 3,  none).
rule_src(r_m05,  qd5339, 3, 4,  none).
rule_src(r_m06,  qd5339, 3, 5,  a).
rule_src(r_m07,  qd5339, 0, none, none).      % Phụ lục 1 (không thuộc điều nào)
rule_src(r_m10,  qd5339, 3, 6,  none).
rule_src(r_m13,  qd5339, 3, 9,  none).
rule_src(r_m14,  qd5339, 3, 10, none).
rule_src(r_m15,  qd5339, 3, 11, none).
rule_src(r_m16,  qd5339, 2, 6,  none).

%% ---------------------------------------------------------------------------
%% 1. PHÂN BIỆT HAI TRẠNG THÁI: ĐỦ ĐIỀU KIỆN XIN MIỄN  vs  ĐÃ ĐƯỢC MIỄN
%%    Điều 2 khoản 6 (R-M16) — QD-11.
%%
%%    Đây là quy tắc quan trọng nhất của file này. Miễn KHÔNG tự động: có chứng
%%    chỉ chỉ sinh du_dk_xin_mien/1; chỉ quyết định phê duyệt mới sinh
%%    duoc_mien/1. KHÔNG có luật nào suy passed(C) từ du_dk_xin_mien(C).
%% ---------------------------------------------------------------------------
why(du_dk_xin_mien(C), r_m16) :- du_dk_xin_mien(C).

%% chỉ dữ kiện ngoài (quyết định của Tổ Xét miễn) mới sinh duoc_mien/1
diem_m(C) :- duoc_mien(C), hp_dieu_kien(C).
why(diem_m(C), r_m05) :- duoc_mien(C), hp_dieu_kien(C).

%% cảnh báo suy diễn: đủ điều kiện nhưng CHƯA có quyết định → chưa được miễn
mien_treo(C) :- du_dk_xin_mien(C), not duoc_mien(C).
why(mien_treo(C), r_m16) :- mien_treo(C).

%% ---------------------------------------------------------------------------
%% 2. NGƯỠNG TÍCH LŨY RIÊNG CHO GDQP&AN — Điều 3 khoản 2 (R-M03a)
%%    "trừ học phần Giáo dục quốc phòng và an ninh phải đạt từ điểm D+ trở lên"
%%    D+ = 1,5 thang 4 → g4 ≥ 15 (chặt hơn ngưỡng D = 10 của QĐ3266 Điều 22 k.3)
%% ---------------------------------------------------------------------------
khong_dat_gdqp(C) :- loai_hp(C,gdqp), g4(C,P), P < 15.
why(khong_dat_gdqp(C), r_m03a) :- khong_dat_gdqp(C).

%% ---------------------------------------------------------------------------
%% 3. QUY ĐỔI ĐIỂM CHO ĐIỂM CHUYỂN TỪ CƠ SỞ ĐÀO TẠO KHÁC — Điều 3 khoản 2
%%    (R-M02 bảng quy đổi, R-M03b ngưỡng tích lũy 5,0)
%%
%%    QD-09 — ĐÃ ĐÓNG. Hai văn bản cùng hiệu lực quy định khác nhau; phân giải
%%    theo PHẠM VI ÁP DỤNG, không theo thời điểm ban hành:
%%      · điểm HỌC TẠI ĐHCT      → bảng QĐ3266, ngưỡng tích lũy 4,0  (D)
%%      · điểm CHUYỂN ĐỔI        → bảng QĐ5339, ngưỡng tích lũy 5,0  (D+)
%%    Điểm chuyển đổi 4,0–4,9 KHÔNG được tích lũy.
%%
%%    LƯU Ý VỀ CHỨNG CHỈ: phân giải này KHÔNG nằm trong câu chữ của văn bản nào —
%%    nó là một quyết định diễn giải do con người xác nhận. Vì vậy mọi kết luận
%%    dựa vào nó phát kèm dien_giai(qd09) để chứng chỉ nói rõ điều đó, thay vì
%%    trình bày như thể suy trực tiếp từ quy chế.
%% ---------------------------------------------------------------------------
band_ngoai(90,100, 40).
band_ngoai(80, 89, 35).
band_ngoai(70, 79, 30).
band_ngoai(65, 69, 25).
band_ngoai(55, 64, 20).
band_ngoai(50, 54, 15).

g4_chuyen(C,P) :- g10_ngoai(C,X), band_ngoai(Lo,Hi,P), X >= Lo, X <= Hi.
why(g4_chuyen(C,P), r_m02) :- g4_chuyen(C,P).

%% ngưỡng tích lũy của điểm chuyển đổi là 5,0 thang 10 (R-M03b)
tich_luy_chuyen(C)      :- g10_ngoai(C,X), X >= 50.
khong_tich_luy_chuyen(C) :- g10_ngoai(C,X), X < 50.
why(tich_luy_chuyen(C), r_m03b)       :- tich_luy_chuyen(C).
why(khong_tich_luy_chuyen(C), r_m03b) :- khong_tich_luy_chuyen(C).

%% BẤT ĐỐI XỨNG do QD-09: cùng con số 4,0–4,9 thì tích lũy được nếu học tại ĐHCT
%% và KHÔNG tích lũy được nếu chuyển từ trường khác. Đánh dấu để chứng chỉ nêu rõ
%% đây là hệ quả của một quyết định diễn giải, không phải của một điều khoản.
bat_doi_xung_qd09(C) :- g10_ngoai(C,X), X >= 40, X < 50.
dien_giai(qd09)      :- bat_doi_xung_qd09(_).
why(bat_doi_xung_qd09(C), r_m03b) :- bat_doi_xung_qd09(C).

%% ---------------------------------------------------------------------------
%% 4. GỘP ĐIỂM KHI XÉT MIỄN — Điều 3 khoản 3 (R-M04) — QD-10
%%    (a) nhiều học phần đã học  →  1 học phần được miễn : trung bình có trọng số
%%    (b) 1 học phần đã học      →  nhiều học phần được miễn : giữ nguyên điểm
%%    mien_tu(HocPhanDuocMien, HocPhanDaHoc) là dữ kiện từ quyết định xét miễn.
%% ---------------------------------------------------------------------------
so_nguon(C,N) :- duoc_mien(C), N = #count{ S : mien_tu(C,S) }.

%% (a) nhiều → một
mien_tu_tu(C,Num)  :- so_nguon(C,N), N > 1,
                      Num = #sum{ P*CR,S : mien_tu(C,S), g4_da_hoc(S,P), tc_da_hoc(S,CR) }.
mien_tu_mau(C,Den) :- so_nguon(C,N), N > 1,
                      Den = #sum{ CR,S   : mien_tu(C,S), tc_da_hoc(S,CR) }.
g4(C,P) :- mien_tu_tu(C,Num), mien_tu_mau(C,Den), Den > 0, P = Num/Den.
why(g4(C,P), r_m04) :- mien_tu_tu(C,Num), mien_tu_mau(C,Den), Den > 0, P = Num/Den.

%% (b) một → nhiều  (một học phần đã học được dùng cho nhiều học phần được miễn)
g4(C,P) :- so_nguon(C,1), mien_tu(C,S), g4_da_hoc(S,P).
why(g4(C,P), r_m04) :- so_nguon(C,1), mien_tu(C,S), g4_da_hoc(S,P).

%% ---------------------------------------------------------------------------
%% 5. BẢNG QUY ĐỔI CHỨNG CHỈ NGOẠI NGỮ — Phụ lục 1 (R-M07)
%%    Điểm số nhân 10 để giữ số nguyên (IELTS 4.5 → 45).
%%    bac_toi_thieu(LoaiChungChi, DiemX10, Bac) : đạt Điểm ⇒ đạt Bậc.
%% ---------------------------------------------------------------------------
nguong_cc(ielts,     30, 2).  nguong_cc(ielts,     45, 3).
nguong_cc(ielts,     55, 4).  nguong_cc(ielts,     65, 5).
nguong_cc(ielts,     75, 6).
nguong_cc(toeic,   4000, 2).  nguong_cc(toeic,   4500, 3).
nguong_cc(toeic,   6000, 4).  nguong_cc(toeic,   8500, 5).
nguong_cc(toeic,   9450, 6).
nguong_cc(toefl_itp, 3370, 2). nguong_cc(toefl_itp, 4500, 3).
nguong_cc(toefl_itp, 5000, 4). nguong_cc(toefl_itp, 5500, 5).
nguong_cc(toefl_itp, 6300, 6).
nguong_cc(toefl_cbt,  960, 2). nguong_cc(toefl_cbt, 1330, 3).
nguong_cc(toefl_cbt, 1730, 4). nguong_cc(toefl_cbt, 2130, 5).
nguong_cc(toefl_cbt, 2500, 6).
nguong_cc(toefl_ibt,  310, 2). nguong_cc(toefl_ibt,  450, 3).
nguong_cc(toefl_ibt,  610, 4). nguong_cc(toefl_ibt,  900, 5).
nguong_cc(toefl_ibt, 1110, 6).
%% chứng chỉ A/B/C do ĐHCT cấp: A=bậc 1, B=bậc 2, C=bậc 3
nguong_cc(ctu_abc, 1, 1). nguong_cc(ctu_abc, 2, 2). nguong_cc(ctu_abc, 3, 3).

%% Ngôn ngữ của chứng chỉ (sửa 09/10/2026). Toàn bộ bảng trên là mục 1 "Tiếng Anh" của
%% Phụ lục 1; ctu_abc = chứng chỉ TIẾNG ANH A/B/C do ĐHCT cấp. Bảng tiếng Pháp (mục 2,
%% trang 12) CHƯA chép — OCR không đọc được — nên miễn Pháp văn hiện KHÔNG suy được (P).
ngon_ngu_cc(ielts,anh). ngon_ngu_cc(toeic,anh). ngon_ngu_cc(toefl_itp,anh).
ngon_ngu_cc(toefl_cbt,anh). ngon_ngu_cc(toefl_ibt,anh). ngon_ngu_cc(ctu_abc,anh).

bac_nn(NN,B) :- chung_chi(L,S), nguong_cc(L,Min,B), ngon_ngu_cc(L,NN), S >= Min.
bac_ngoai_ngu(B) :- bac_nn(_,B).
why(bac_ngoai_ngu(B), r_m07) :- bac_ngoai_ngu(B).

%% ---------------------------------------------------------------------------
%% 6. MIỄN HỌC PHẦN ANH VĂN CĂN BẢN — Điều 3 khoản 5 điểm a (R-M06)
%%    Khóa 45 trở về sau: cần BẬC 3 trở lên (Khóa 44 trở về trước: bậc 2).
%%    Chứng chỉ phải CÙNG NGÔN NGỮ với học phần: điểm a = tiếng Anh → Anh văn,
%%    điểm b = tiếng Pháp → Pháp văn. (v1.4 gộp hai điểm → IELTS cho xin miễn cả
%%    Pháp văn: dương tính giả, phát hiện ở Tuần 7.) ngon_ngu_hp/2 lấy từ CTĐT.
%% ---------------------------------------------------------------------------
nguong_bac_mien(3) :- khoa_tu_k45.
nguong_bac_mien(2) :- not khoa_tu_k45.

du_dk_xin_mien(C) :- loai_hp(C, ngoai_ngu_cb), ngon_ngu_hp(C,NN), bac_nn(NN,B),
                     nguong_bac_mien(Min), B >= Min.
why(du_dk_xin_mien(C), r_m06) :- loai_hp(C, ngoai_ngu_cb), ngon_ngu_hp(C,NN), bac_nn(NN,B),
                                 nguong_bac_mien(Min), B >= Min.

%% ---------------------------------------------------------------------------
%% 7. MIỄN HỌC PHẦN TIN HỌC CĂN BẢN — Điều 3 khoản 6 (R-M10)
%% ---------------------------------------------------------------------------
cc_tin_hoc_hop_le :- chung_chi_tin_hoc(_).
cc_tin_hoc_hop_le :- bang_nhom_nganh_cntt.

du_dk_xin_mien(C) :- loai_hp(C, tin_hoc_cb), cc_tin_hoc_hop_le.
why(du_dk_xin_mien(C), r_m10) :- loai_hp(C, tin_hoc_cb), cc_tin_hoc_hop_le.

%% ---------------------------------------------------------------------------
%% 8. BẢNG CHUYỂN ĐỔI LÝ LUẬN CHÍNH TRỊ — Điều 3 khoản 9 (R-M13)
%%    Ngành KHÔNG chuyên về Lý luận chính trị (áp dụng cho CNTT).
%%    ml_thay(HocPhanCu, HocPhanMoi) — chú ý ML010 là ca MỘT → NHIỀU.
%% ---------------------------------------------------------------------------
ml_thay("ML009", "ML014").
ml_thay("ML010", "ML016").
ml_thay("ML010", "ML018").
ml_thay("ML011", "ML019").
ml_thay("ML006", "ML021").

mien_tu(New, Old) :- ml_thay(Old, New), passed(Old).
why(mien_tu(New,Old), r_m13) :- mien_tu(New,Old), ml_thay(Old,New).

%% ---------------------------------------------------------------------------
%% 9. MIỄN THI DO THÀNH TÍCH OLYMPIC / ROBOCON — Điều 3 khoản 10 (R-M14)
%%    Ràng buộc: ≤ 4 TC mỗi học phần; ≤ 2 học phần trong một học kỳ;
%%    nếu điểm học thật cao hơn thì lấy điểm học thật.
%% ---------------------------------------------------------------------------
diem_thanh_tich(giai_nhat,   100).
diem_thanh_tich(giai_nhi,    100).
diem_thanh_tich(giai_ba,     100).
diem_thanh_tich(khuyen_khich, 89).
diem_thanh_tich(thanh_vien,   79).

%% hợp lệ chỉ khi học phần ≤ 4 TC
mien_thi_hop_le(C) :- mien_thi(C,_), course(C,CR), CR <= 4.
why(mien_thi_hop_le(C), r_m14) :- mien_thi_hop_le(C).

vuot_han_mien_thi(K) :- hoc_ky(K), #count{ C : mien_thi(C,_), hoc_trong_hk(K,C) } > 2.
why(vuot_han_mien_thi(K), r_m14) :- vuot_han_mien_thi(K).

%% điểm cuối = max(điểm thành tích, điểm học thật)
g10(C,X) :- mien_thi_hop_le(C), mien_thi(C,T), diem_thanh_tich(T,X),
            not diem_hoc_cao_hon(C).
diem_hoc_cao_hon(C) :- mien_thi(C,T), diem_thanh_tich(T,X), g10_hoc(C,Y), Y > X.
g10(C,Y) :- diem_hoc_cao_hon(C), g10_hoc(C,Y).
why(g10(C,X), r_m14) :- mien_thi_hop_le(C), g10(C,X).

%% ---------------------------------------------------------------------------
%% 10. ĐIỂM XÉT MIỄN CÓ VÀO ĐTBCTL HAY KHÔNG — Điều 3 khoản 11 (R-M15)
%%     "Trừ các học phần điều kiện và học phần có điểm M, kết quả điểm xét miễn
%%      học phần được sử dụng để tính điểm trung bình chung tích lũy."
%%
%%     SỬA QD-01 của v1.0. Hai trạng thái khác nhau:
%%       exempted_M   — học phần điều kiện, điểm M : vào TC, KHÔNG vào ĐTBCTL
%%       recognized   — công nhận điểm            : vào TC VÀ vào ĐTBCTL
%%     Trong qd3266_r_formal_v1.lp, tl_tu/tl_mau đã loại khong_tinh_tb(C) và
%%     hp_dieu_kien(C); các học phần recognized KHÔNG thuộc hai nhóm đó nên tự
%%     động được tính — quy tắc dưới đây phát why/2 để chứng chỉ nói rõ điều này.
%% ---------------------------------------------------------------------------
recognized(C) :- duoc_mien(C), not hp_dieu_kien(C), not diem_m(C).
why(recognized(C), r_m15) :- recognized(C).

exempted_m(C) :- duoc_mien(C), diem_m(C).
why(exempted_m(C), r_m15) :- exempted_m(C).

vao_dtbctl(C) :- recognized(C), g4(C,_).
why(vao_dtbctl(C), r_m15) :- vao_dtbctl(C).

#show mien_treo/1.
#show recognized/1.
#show exempted_m/1.
#show tich_luy_chuyen/1.
#show khong_tich_luy_chuyen/1.
#show bat_doi_xung_qd09/1.
#show dien_giai/1.
