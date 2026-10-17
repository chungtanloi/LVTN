%%=============================================================================
%% qd3266_r_formal_v1.lp — R-Formal v1 (v1.7: thời gian tối đa là điều kiện tốt nghiệp — Tuần 16)
%% Hình thức hoá các điều khoản lớp F của QĐ 3266/QĐ-ĐHCT (15/8/2024)
%% Dự án: CPA² — Certified Personalized Academic Advising (Tuần 5/24)
%%
%% LƯỢC ĐỒ CON TRỎ NGUỒN (chốt ở Tuần 5, trả lời câu hỏi thiết kế số 2 của Tuần 4)
%%   rule_src(RuleId, VanBan, Dieu, Khoan, Diem).   con trỏ tới văn bản/điều/khoản/điểm
%%   (v1.1: bổ sung tham số VanBan — một KB nay trải trên NHIỀU văn bản quy phạm)
%%   why(Atom, RuleId).                        vì sao Atom được suy ra
%% BẤT BIẾN (kiểm tự động bằng validate_rformal.py):
%%   (1) mọi RuleId xuất hiện trong why/2 đều có rule_src/5;
%%   (2) mọi rule_src/5 đều có bản ghi tương ứng trong r_formal_v1.json;
%%   (3) mọi quy tắc suy ra kết luận về SV đều phát kèm một why/2.
%%
%% QUY ƯỚC SỐ HỌC: clingo chỉ có số nguyên.
%%   g10(C,X)   điểm thang 10  ×10   (7,5 → 75)
%%   g4(C,P)    điểm thang 4   ×10   (2,50 → 25)
%%   Mọi so sánh trung bình dùng dạng nhân chéo, không dùng phép chia.
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 0. CON TRỎ NGUỒN
%% ---------------------------------------------------------------------------
rule_src(r_a01, qd3266, 7, 2, none).
rule_src(r_a02, qd3266, 7, 3, none).
rule_src(r_a03, qd3266, 7, 4, none).
rule_src(r_a04, qd3266, 7, 5, none).
rule_src(r_a05, qd3266, 7, 6, none).
rule_src(r_b02, qd3266, 22, 2, none).
rule_src(r_b03, qd3266, 22, 3, none).
rule_src(r_b04, qd3266, 22, 5, a).
rule_src(r_b05, qd3266, 22, 5, b).
rule_src(r_b06, qd3266, 22, 5, c).
rule_src(r_b07, qd3266, 24, 1, none).
rule_src(r_b08, qd3266, 24, 2, none).
rule_src(r_b09, qd3266, 24, 3, none).
rule_src(r_b10, qd3266, 24, 4, none).
rule_src(r_b11, qd3266, 24, 5, none).
rule_src(r_b12, qd3266, 17, 1, none).
rule_src(r_b13, qd3266, 17, 2, none).
rule_src(r_b14, qd3266, 17, 3, none).
rule_src(r_c01, qd3266, 14, 1, none).
rule_src(r_c02, qd3266, 14, 2, none).
rule_src(r_c04, qd3266, 15, none, none).
rule_src(r_d01, qd3266, 18, 2, a).
rule_src(r_d03, qd3266, 18, 2, c).
rule_src(r_d04, qd3266, 18, 2, c).
rule_src(r_d06, qd3266, 18, 5, b).
rule_src(r_d08, qd3266, 18, 5, g).
rule_src(r_e01, qd3266,  5, none, none).
rule_src(r_e02, qd3266,  5, none, none).
rule_src(r_e03, qd3266, 30, none, none).
rule_src(r_f01a, qd3266, 32, 1, a).
rule_src(r_f02a, qd3266, 32, 1, b).
rule_src(r_f03, qd3266,  32, 1, c).
rule_src(r_f05, qd3266,  31, 3, none).
rule_src(r_f06, qd3266,  34, 2, none).
rule_src(r_f07, qd3266,  34, 2, a).
rule_src(r_f09, qd3266,  33, 1, none).
rule_src(r_f10, qd3266,  33, 2, none).
rule_src(r_g01, qd3266,  20, 1, b).
rule_src(r_g02, qd3266,  20, 7, none).
rule_src(r_g03, qd3266,  20, 8, none).
rule_src(r_h01, qd3266,  12, 4, b).

%% ---------------------------------------------------------------------------
%% 1. QUY ĐỔI ĐIỂM — Điều 22 khoản 2 (R-B02)
%%    Bảng quy đổi thang 10 → điểm chữ → thang 4.
%% ---------------------------------------------------------------------------
band(90,100,"A", 40).
band(80, 89,"B+",35).
band(70, 79,"B", 30).
band(65, 69,"C+",25).
band(55, 64,"C", 20).
band(50, 54,"D+",15).
band(40, 49,"D", 10).
band( 0, 39,"F",  0).

letter(C,L) :- g10(C,X), band(Lo,Hi,L,_), X >= Lo, X <= Hi.
g4(C,P)     :- g10(C,X), band(Lo,Hi,_,P), X >= Lo, X <= Hi.
why(g4(C,P), r_b02) :- g4(C,P).

%% ---------------------------------------------------------------------------
%% 2. TÍCH LŨY HỌC PHẦN — Điều 22 khoản 3 (R-B03) và khoản 5 điểm a (R-B04)
%%    "Học phần chỉ được tính tích lũy khi đạt từ điểm D trở lên."  D = 1,0 → g4 ≥ 10
%%    "Điểm M ... không tính vào ĐTBCHK và ĐTBCTL. Số TC của học phần có điểm M
%%     được tính vào tổng số TC tích lũy."
%% ---------------------------------------------------------------------------
passed(C) :- g4(C,P), P >= 10.
why(passed(C), r_b03) :- g4(C,P), P >= 10.

passed(C) :- diem_m(C).                       % học phần được miễn: điểm M
why(passed(C), r_b04) :- diem_m(C).

%% ---------------------------------------------------------------------------
%% 2b. HỌC PHẦN ĐƯỢC TÍNH TÍCH LŨY — CQ-06 (v1.5, Tuần 6)
%%     Khi xét tốt nghiệp, SV được CHỌN học phần tự chọn nào đưa vào tích lũy
%%     (vd. làm cả LVTN và TLTN, hoặc học dư tự chọn). Học phần tự chọn đã đạt mà
%%     SV không chọn: vẫn là "đã đạt" (thỏa tiên quyết) nhưng KHÔNG vào số TC tích
%%     lũy, ĐTBCTL hay nhóm tự chọn. Chỉ học phần thuộc nhóm tự chọn mới loại được
%%     (ràng buộc ở curriculum_schema.lp). Không có dữ kiện khong_tinh_tich_luy/1
%%     → mọi học phần đạt đều được tính, đúng như v1.4.
%%     NGUỒN: xác nhận thực tiễn xét tốt nghiệp (Loi, 19/9/2026) — CHƯA có trích
%%     văn bản; mọi kết luận dùng quyền chọn này phát kèm dien_giai(cq06).
%% ---------------------------------------------------------------------------
tich_luy(C) :- passed(C), not khong_tinh_tich_luy(C).
dien_giai(cq06) :- khong_tinh_tich_luy(_).

%% Điểm M / W / I không tham gia tính trung bình (R-B04, R-B06, R-B05)
khong_tinh_tb(C) :- diem_m(C).
khong_tinh_tb(C) :- diem_w(C).
why(khong_tinh_tb(C), r_b04) :- diem_m(C).
why(khong_tinh_tb(C), r_b06) :- diem_w(C).

%% Điểm I: KHÔNG tính vào ĐTBCHK của HK đó; trạng thái tích lũy chưa xác định
%% (R-B05, lớp P — quá 1 năm mới thành F, thời hạn cụ thể do GV quy định).
khong_tinh_hk(C) :- diem_i(C).
why(khong_tinh_hk(C), r_b05) :- diem_i(C).

%% ---------------------------------------------------------------------------
%% 3. HỌC PHẦN ĐIỀU KIỆN — Điều 7 khoản 6 (R-A05)
%%    Phải hoàn thành, nhưng không dùng để tính ĐTBCTL; riêng GDTC còn không
%%    dùng để tính ĐTBCHK và ĐTBCNH.
%% ---------------------------------------------------------------------------
hp_dieu_kien(C) :- loai_hp(C, gdqp).
hp_dieu_kien(C) :- loai_hp(C, gdtc).
hp_dieu_kien(C) :- loai_hp(C, ngoai_ngu_cb).
hp_dieu_kien(C) :- loai_hp(C, tin_hoc_cb).
why(hp_dieu_kien(C), r_a05) :- hp_dieu_kien(C).

%% ---------------------------------------------------------------------------
%% 4. HỌC PHẦN BẮT BUỘC / TỰ CHỌN — Điều 7 khoản 2, 3 (R-A01, R-A02)
%% ---------------------------------------------------------------------------
thieu_bat_buoc(C) :- bat_buoc(C), not passed(C).
why(thieu_bat_buoc(C), r_a01) :- thieu_bat_buoc(C).

dat_nhom(G) :- group_min(G,N), #count{ C : in_group(G,C), tich_luy(C) } >= N.
why(dat_nhom(G), r_a02) :- dat_nhom(G).
%% v1.5: nhóm đếm-môn là MỘT kiểu nhóm tự chọn; kiểu đếm-tín-chỉ và kiểu một-nhánh
%% (CTĐT thật dùng) nằm ở w6_curriculum/curriculum_schema.lp, cũng sinh nhom_tu_chon/1.
nhom_tu_chon(G) :- group_min(G,_).

%% ---------------------------------------------------------------------------
%% 5. TIÊN QUYẾT & SONG HÀNH — Điều 7 khoản 4, 5 (R-A03, R-A04)
%%    Điều kiện tiên quyết là ĐÃ TÍCH LŨY, không phải "đã học".
%% ---------------------------------------------------------------------------
%% v1.5 (Tuần 6, lỗi L3): tiên quyết có HAI dạng — T4a học phần→học phần và T4b
%% NGƯỠNG TÍN CHỈ TÍCH LŨY ("≥120TC" trong CTĐT). Bản v1.4 chỉ xét T4a nên kết luận
%% CT550E "được đăng ký" với sinh viên mới có 30 TC. Cả hai cùng nguồn R-A03.
du_dk_tc(C)   :- tien_quyet_tc(C,N), tc_tich_luy(T), T >= N.
thieu_tc(C,D) :- tien_quyet_tc(C,N), tc_tich_luy(T), T < N, D = N - T.
why(du_dk_tc(C), r_a03)   :- du_dk_tc(C).
why(thieu_tc(C,D), r_a03) :- thieu_tc(C,D).

du_dk_dang_ky(C) :- course(C,_), passed(P) : tien_quyet(C,P); not thieu_tc(C,_).
why(du_dk_dang_ky(C), r_a03) :- du_dk_dang_ky(C).

vi_pham_song_hanh(C,P) :- xep_hk(C,K1), song_hanh(C,P), xep_hk(P,K2), K2 > K1.
why(vi_pham_song_hanh(C,P), r_a04) :- vi_pham_song_hanh(C,P).

%% ---------------------------------------------------------------------------
%% 6. SỐ TÍN CHỈ ĐĂNG KÝ — Điều 14 khoản 1, 2 (R-C01, R-C02)
%%    LƯU Ý: quy chế KHÔNG có sàn tín chỉ đăng ký (xem R-C03, phát hiện âm tính).
%% ---------------------------------------------------------------------------
tran_tc_hk(20).
vuot_tran_dang_ky(K) :- tong_tc_dang_ky(K,T), tran_tc_hk(M), T > M.
why(vuot_tran_dang_ky(K), r_c01) :- vuot_tran_dang_ky(K).

khong_can_dang_ky(K) :- hk_dau_khoa(K).
why(khong_can_dang_ky(K), r_c02) :- khong_can_dang_ky(K).

%% ---------------------------------------------------------------------------
%% 7. TÍN CHỈ TÍCH LŨY & TRUNG BÌNH CHUNG — Điều 24 (R-B07, R-B08, R-B10)
%%    ĐTBCTL: chỉ học phần ĐÃ TÍCH LŨY, KHÔNG gồm điểm F và học phần điều kiện.
%%    ĐTBCHK: gồm CẢ điểm F và học phần điều kiện, TRỪ GDTC.
%% ---------------------------------------------------------------------------
tc_tich_luy(T) :- T = #sum{ CR,C : course(C,CR), tich_luy(C) }.
why(tc_tich_luy(T), r_b07) :- tc_tich_luy(T).

%% --- ĐTBCTL (×10) dưới dạng tử số / mẫu số, so sánh bằng nhân chéo ----------
tl_tu(N) :- N = #sum{ P*CR,C : course(C,CR), g4(C,P), tich_luy(C),
                              not hp_dieu_kien(C), not khong_tinh_tb(C) }.
tl_mau(D) :- D = #sum{ CR,C  : course(C,CR), g4(C,_), tich_luy(C),
                              not hp_dieu_kien(C), not khong_tinh_tb(C) }.
why(tl_tu(N), r_b10) :- tl_tu(N).
why(tl_mau(D), r_b10) :- tl_mau(D).

%% dtbctl_ge(V): ĐTBCTL ≥ V/10  ⇔  tử ≥ V × mẫu
dtbctl_ge(V) :- nguong(V), tl_tu(N), tl_mau(D), D > 0, N >= V*D.
dtbctl_lt(V) :- nguong(V), tl_tu(N), tl_mau(D), D > 0, N <  V*D.

%% --- ĐTBCHK (×10) của học kỳ K ---------------------------------------------
hk_tu(K,N) :- hoc_ky(K), N = #sum{ P*CR,C : hoc_trong_hk(K,C), course(C,CR), g4(C,P),
                                   not loai_hp(C,gdtc), not khong_tinh_tb(C),
                                   not khong_tinh_hk(C) }.
hk_mau(K,D) :- hoc_ky(K), D = #sum{ CR,C : hoc_trong_hk(K,C), course(C,CR), g4(C,_),
                                   not loai_hp(C,gdtc), not khong_tinh_tb(C),
                                   not khong_tinh_hk(C) }.
why(hk_tu(K,N), r_b08) :- hk_tu(K,N).

dtbchk_lt(K,V) :- nguong(V), hk_tu(K,N), hk_mau(K,D), D > 0, N < V*D.
dtbchk_ge(K,V) :- nguong(V), hk_tu(K,N), hk_mau(K,D), D > 0, N >= V*D.

%% ---------------------------------------------------------------------------
%% 8. XẾP TRÌNH ĐỘ NĂM HỌC — Điều 30 (R-E03), cột "từ K.45 trở về sau"
%% ---------------------------------------------------------------------------
bac_nam(1,  0,  35).
bac_nam(2, 36,  70).
bac_nam(3, 71, 105).
bac_nam(4,106, 141).
bac_nam(5,142, 1000).

trinh_do_nam(Y) :- tc_tich_luy(T), bac_nam(Y,Lo,Hi), T >= Lo, T <= Hi, khoa_tu_k45.
why(trinh_do_nam(Y), r_e03) :- trinh_do_nam(Y).

%% ---------------------------------------------------------------------------
%% 9. CẢNH BÁO HỌC TẬP — Điều 18 khoản 2 (R-D01, R-D03, R-D04)
%% ---------------------------------------------------------------------------
nguong(8;10;12;14;16;18;20;25;32;36).      % các ngưỡng ×10 dùng trong quy chế

%% a) ĐTBCHK < 0,80 ở HK đầu khóa; < 1,00 ở các HK tiếp theo
canh_bao(K) :- hk_dau_khoa(K), dtbchk_lt(K,8).
canh_bao(K) :- hoc_ky(K), not hk_dau_khoa(K), dtbchk_lt(K,10).
why(canh_bao(K), r_d01) :- hk_dau_khoa(K), dtbchk_lt(K,8).
why(canh_bao(K), r_d01) :- hoc_ky(K), not hk_dau_khoa(K), dtbchk_lt(K,10).

%% c) K47+ : TC không đạt trong HK > 50% khối lượng đã đăng ký
canh_bao(K) :- khoa_tu_k47, tc_khong_dat(K,X), tong_tc_dang_ky(K,T), 2*X > T.
why(canh_bao(K), r_d03) :- khoa_tu_k47, tc_khong_dat(K,X), tong_tc_dang_ky(K,T), 2*X > T.

%%    K47+ : tổng TC nợ đọng từ đầu khóa > 24 TC
%%    (QD-03: "TC nợ đọng" do CPA² định nghĩa — xem r_formal_v1.json)
canh_bao(K) :- khoa_tu_k47, hoc_ky(K), tc_no_dong(K,X), X > 24.
why(canh_bao(K), r_d03) :- khoa_tu_k47, hoc_ky(K), tc_no_dong(K,X), X > 24.

%%    K47+ : ĐTBCTL dưới ngưỡng theo trình độ năm học
nguong_tl(1,12). nguong_tl(2,14). nguong_tl(3,16).
nguong_tl(4,18). nguong_tl(5,18).
canh_bao(K) :- khoa_tu_k47, hoc_ky(K), trinh_do_nam(Y), nguong_tl(Y,V), dtbctl_lt(V).
why(canh_bao(K), r_d04) :- khoa_tu_k47, hoc_ky(K), trinh_do_nam(Y),
                           nguong_tl(Y,V), dtbctl_lt(V).

%% ---------------------------------------------------------------------------
%% 9b. ĐỊNH NGHĨA VẬN HÀNH CỦA "TC NỢ ĐỌNG" — QD-03
%%     QĐ3266 dùng thuật ngữ "TC nợ đọng" ĐÚNG MỘT LẦN (Điều 18 k.2 đ.c) và KHÔNG
%%     định nghĩa nó ở bất kỳ đâu. Định nghĩa dưới đây là DIỄN GIẢI, không phải
%%     câu chữ quy chế — mọi kết luận dùng nó đều phát kèm dien_giai(qd03).
%%
%%     Định nghĩa: TC nợ đọng = tổng TC của các học phần ĐÃ ĐĂNG KÝ từ đầu khoá
%%     mà đến thời điểm xét vẫn CHƯA TÍCH LŨY.
%%
%%     Hai câu hỏi con mà định nghĩa trên KHÔNG trả lời, nên để thành chính sách
%%     bật/tắt thay vì chôn cứng — hai chính sách cho hai con số khác nhau:
%%       QD-03a: học phần ĐANG HỌC (chưa có điểm) có tính là nợ không?
%%               mặc định CÓ  → chinh_sach(tinh_dang_hoc) được bật sẵn bên dưới
%%       QD-03b: học phần đã RÚT hợp lệ (điểm W) có tính là nợ không?
%%               mặc định KHÔNG — vì Điều 15 cho phép rút và Điều 22 k.5 đ.c loại
%%               điểm W khỏi mọi trung bình; coi môn đã rút hợp lệ là "nợ" sẽ
%%               phạt sinh viên vì một quyền mà quy chế trao cho họ.
%%
%%     Toàn bộ khối này chỉ chạy khi có dữ kiện che_do(suy_no_dong); nếu không,
%%     tc_no_dong/2 vẫn là dữ kiện ngoài như trước (ví dụ lấy thẳng từ hệ thống
%%     quản lý trực tuyến của Trường).
%% ---------------------------------------------------------------------------
chinh_sach(tinh_dang_hoc) :- che_do(suy_no_dong), not chinh_sach_tat(tinh_dang_hoc).
chinh_sach(tinh_diem_w)   :- che_do(suy_no_dong), chinh_sach_bat(tinh_diem_w).

da_dang_ky(C) :- dang_ky(_,C).

bo_khoi_no_dong(C) :- diem_w(C),  not chinh_sach(tinh_diem_w).
bo_khoi_no_dong(C) :- dang_hoc(C), not chinh_sach(tinh_dang_hoc).

no_dong(C) :- che_do(suy_no_dong), da_dang_ky(C),
              not passed(C), not bo_khoi_no_dong(C).
why(no_dong(C), r_d03) :- no_dong(C).

tc_no_dong_suy(X) :- che_do(suy_no_dong),
                     X = #sum{ CR,C : no_dong(C), course(C,CR) }.
tc_no_dong(K,X)   :- hoc_ky(K), tc_no_dong_suy(X).
dien_giai(qd03)   :- tc_no_dong_suy(_).
why(tc_no_dong(K,X), r_d03) :- tc_no_dong(K,X).

%% ---------------------------------------------------------------------------
%% 10. XEM XÉT BUỘC THÔI HỌC — Điều 18 khoản 5 điểm b, g (R-D06 lớp P, R-D08)
%%     QD-04: vì có mệnh đề "trường hợp đặc biệt do Hiệu trưởng quyết định",
%%     CPA² chỉ kết luận "THUỘC DIỆN XEM XÉT", không kết luận buộc thôi học.
%% ---------------------------------------------------------------------------
dien_xem_xet_thoi_hoc(K2) :- canh_bao(K1), ke_tiep(K1,K2), dtbchk_lt(K2,10).
why(dien_xem_xet_thoi_hoc(K2), r_d06) :- dien_xem_xet_thoi_hoc(K2).

dien_xem_xet_thoi_hoc(K) :- hoc_ky(K), qua_thoi_gian_toi_da.
why(dien_xem_xet_thoi_hoc(K), r_d08) :- hoc_ky(K), qua_thoi_gian_toi_da.

%% ---------------------------------------------------------------------------
%% 11. THỜI GIAN HỌC TẬP TỐI ĐA — Điều 5 (R-E01, R-E02)
%%     thiet_ke_nam(N) tính bằng nửa năm ×2 để biểu diễn 4,5 năm = 9.
%% ---------------------------------------------------------------------------
tran_nam2(8,  16).      % thiết kế 4   năm (8 nửa năm)  → tối đa 8  năm (16 nửa năm)
tran_nam2(9,  18).      % thiết kế 4,5 năm              → tối đa 9  năm
tran_nam2(10, 20).      % thiết kế 5   năm              → tối đa 10 năm

thoi_gian_toi_da(M) :- thiet_ke_nam2(D), tran_nam2(D,M0), giam_hk(H), M = M0 - H.
why(thoi_gian_toi_da(M), r_e01) :- thoi_gian_toi_da(M).

%% Giảm trần theo TC được công nhận: K49 trở về trước mỗi 9 TC giảm 1 HK
%% (1 HK = 1 nửa năm trong đơn vị nam2 nếu tính 2 HK chính/năm).
giam_hk(H) :- tc_cong_nhan(X), khoa_den_k49, H = X/9.
giam_hk(H) :- tc_cong_nhan(X), khoa_tu_k50, H = X/6.
giam_hk(0) :- not tc_cong_nhan(_).          % không được công nhận TC nào
why(giam_hk(H), r_e02) :- giam_hk(H).

qua_thoi_gian_toi_da :- da_hoc_nam2(A), thoi_gian_toi_da(M), A > M.

%% ---------------------------------------------------------------------------
%% 12. ĐIỀU KIỆN TỐT NGHIỆP — Điều 32 khoản 1 (R-F01a, R-F02a, R-F03)
%% ---------------------------------------------------------------------------
%% a) đủ học phần bắt buộc + đủ nhóm tự chọn + đủ TC + ĐTBCTL ≥ 2,00
dk_bat_buoc   :- not thieu_bat_buoc(_).
%% v1.5 (Tuần 6, lỗi L2): v1.4 chỉ quét group_min/2 (nhóm đếm môn) nên với CTĐT
%% thật — mọi nhóm đều đếm TÍN CHỈ — điều kiện này đúng RỖNG: sinh viên thiếu cả
%% 15 TC nhóm tốt nghiệp vẫn "đủ tự chọn". Đây là lỗi DƯƠNG TÍNH GIẢ (vi phạm tính
%% đúng đắn), nguy hiểm hơn L1. Nhóm điều kiện (toàn học phần (*)) tách sang đ.b.
dk_tu_chon    :- dat_nhom(G) : nhom_tu_chon(G), not nhom_dieu_kien(G).
%% v1.5 — CQ-05 (ĐÓNG, Loi xác nhận 19/9/2026): 161 TC của CTĐT CNTT K49 GỒM 21 TC
%% học phần điều kiện (GDQP 8 + GDTC 3 + ngoại ngữ 10) khi xét đ.a. Hệ quả: SV "chỉ
%% thiếu GDTC" cũng thiếu TC ở đ.a, nên Đ.33 k.2 chỉ kích hoạt khi SV học dư tự chọn
%% bù đúng số TC điều kiện còn thiếu. Chính sách tc_khong_gom_dk (cách đọc BỊ BÁC)
%% giữ lại CHỈ để phân tích độ nhạy — không bật trong vận hành.
dk_tin_chi    :- not chinh_sach_bat(tc_khong_gom_dk),
                 tc_tich_luy(T), tc_toi_thieu_ctdt(M), T >= M.
tc_tl_khong_dk(T) :- T = #sum{ CR,C : course(C,CR), tich_luy(C), not hp_dieu_kien(C) }.
dk_tin_chi    :- chinh_sach_bat(tc_khong_gom_dk), tc_tl_khong_dk(T),
                 tc_toi_thieu_ctdt(M), tc_dk_ctdt(D), T >= M - D.
dien_giai(cq05) :- chinh_sach_bat(tc_khong_gom_dk).
dk_dtbctl     :- dtbctl_ge(20).
why(dk_bat_buoc, r_f01a) :- dk_bat_buoc.
why(dk_tu_chon,  r_f01a) :- dk_tu_chon.
why(dk_tin_chi,  r_f01a) :- dk_tin_chi.
why(dk_dtbctl,   r_f01a) :- dk_dtbctl.

%% b) hoàn thành học phần điều kiện; ĐTB các học phần GDQP&AN ≥ 5,0 (thang 10)
%% v1.5 (Tuần 6, lỗi L1): v1.4 đòi đạt MỌI học phần điều kiện. CTĐT thật cho học
%% phần điều kiện nằm trong nhóm tự chọn ("10 TC AV hoặc PV", GDTC) → v1.4 đòi cả
%% 12 học phần ngoại ngữ (40 TC) và kết luận sai FALSE cho sinh viên đủ điều kiện.
%% Đúng: học phần điều kiện NGOÀI nhóm phải đạt; nhóm điều kiện phải đạt theo nhóm.
dk_hp_dieu_kien :- passed(C) : hp_dieu_kien(C), not hp_trong_nhom(C);
                   dat_nhom(G) : nhom_dieu_kien(G).
gdqp_tu(N)  :- N = #sum{ X*CR,C : loai_hp(C,gdqp), course(C,CR), g10(C,X) }.
gdqp_mau(D) :- D = #sum{ CR,C   : loai_hp(C,gdqp), course(C,CR), g10(C,_) }.
dk_gdqp :- gdqp_tu(N), gdqp_mau(D), D > 0, N >= 50*D.     % 5,0 ×10 = 50
why(dk_hp_dieu_kien, r_f02a) :- dk_hp_dieu_kien.
why(dk_gdqp, r_f02a) :- dk_gdqp.

%% c) trục kỷ luật — DỮ KIỆN KHÔNG TỒN TẠI trong phạm vi CPA² (R-F03).
%%    Không có quy tắc suy ra dk_ky_luat; nó phải đến từ dữ kiện ngoài.
%%    Vì vậy tot_nghiep KHÔNG BAO GIỜ đạt TRUE nếu thiếu dữ kiện này — đúng thiết kế.
truc_ky_luat_khong_co_du_lieu :- not xac_nhan_ky_luat_sach.
why(truc_ky_luat_khong_co_du_lieu, r_f03) :- truc_ky_luat_khong_co_du_lieu.

du_dk_hoc_vu :- dk_bat_buoc, dk_tu_chon, dk_tin_chi, dk_dtbctl,
                dk_hp_dieu_kien, dk_gdqp.
%% v1.7 (Tuần 16, P16-2): phải hoàn thành CTĐT trong thời gian tối đa — Điều 5
%% ("thời gian học tập tối đa cho phép để SV hoàn thành CTĐT", tr.4; R-E01/R-E02).
%% v1.6 bỏ điều kiện này → SV quá hạn vẫn tot_nghiep. Thiếu da_hoc_nam2: ở đây
%% (thế giới đóng) coi như chưa quá hạn; graduation_solver.lp mục 0 mở nhánh → UNKNOWN.
tot_nghiep   :- du_dk_hoc_vu, xac_nhan_ky_luat_sach, not qua_thoi_gian_toi_da.
why(tot_nghiep, r_f01a) :- tot_nghiep.
why(tot_nghiep, r_f03)  :- tot_nghiep.
why(tot_nghiep, r_e01)  :- tot_nghiep.

%% ---------------------------------------------------------------------------
%% 13. HẠNG TỐT NGHIỆP — Điều 34 khoản 2 và điểm a (R-F06, R-F07)
%% ---------------------------------------------------------------------------
hang(xuat_sac, 36, 40).
hang(gioi,     32, 35).
hang(kha,      25, 31).
hang(trung_binh,20, 24).

hang_goc(H) :- hang(H,Lo,Hi), tl_tu(N), tl_mau(D), D > 0, N >= Lo*D, N <= Hi*D.
why(hang_goc(H), r_f06) :- hang_goc(H).

%% giảm một mức nếu TC học phần điểm F > 5% tổng TC quy định của CTĐT
%% (không tính học phần học cải thiện bị điểm F — R-B13)
vuot_5_phan_tram :- tc_diem_f(X), tc_toi_thieu_ctdt(M), 100*X > 5*M.
why(vuot_5_phan_tram, r_f07) :- vuot_5_phan_tram.

giam_mot_muc(xuat_sac, gioi).
giam_mot_muc(gioi, kha).
hang_cuoi(H2) :- hang_goc(H1), giam_mot_muc(H1,H2), vuot_5_phan_tram.
hang_cuoi(H)  :- hang_goc(H), not vuot_5_phan_tram.
hang_cuoi(H)  :- hang_goc(H), vuot_5_phan_tram, not giam_mot_muc(H,_).
why(hang_cuoi(H), r_f07) :- hang_cuoi(H).

%% ---------------------------------------------------------------------------
%% 14. QUÁ HẠN THỜI GIAN HỌC TẬP — Điều 33 khoản 1, 2 (R-F09, R-F10)
%% ---------------------------------------------------------------------------
bi_xoa_ten :- qua_thoi_gian_toi_da, not du_dk_hoc_vu.
why(bi_xoa_ten, r_f09) :- bi_xoa_ten.

%% K47+ : chỉ thiếu GDQP&AN / GDTC / chuẩn đầu ra → được quay lại trong 3 năm
duoc_quay_lai(3) :- khoa_tu_k47, qua_thoi_gian_toi_da,
                    dk_bat_buoc, dk_tu_chon, dk_tin_chi, dk_dtbctl,
                    not dk_hp_dieu_kien.
why(duoc_quay_lai(3), r_f10) :- duoc_quay_lai(3).

%% ---------------------------------------------------------------------------
%% 15. HỌC PHẦN THAY THẾ LUẬN VĂN — Điều 31 khoản 3 (R-F05)
%%     Ràng buộc là ĐỦ SỐ TC theo CTĐT, không phải tương đương từng học phần.
%% ---------------------------------------------------------------------------
thay_the_lvtn_hop_le :- khong_lam_lvtn, tc_tich_luy(T), tc_toi_thieu_ctdt(M), T >= M.
why(thay_the_lvtn_hop_le, r_f05) :- thay_the_lvtn_hop_le.

%% ---------------------------------------------------------------------------
%% 16. HỌC CÙNG LÚC HAI CHƯƠNG TRÌNH — Điều 20 (R-G02, R-G03)
%% ---------------------------------------------------------------------------
phai_dung_ct2(K) :- khoa_tu_k47, hoc_ky(K), dtbctl_lt(20).
phai_dung_ct2(K) :- khoa_tu_k47, canh_bao(K).
why(phai_dung_ct2(K), r_g02) :- phai_dung_ct2(K).

duoc_xet_tn_ct2 :- tot_nghiep, dang_ky_ct2_truoc_2_nam.
why(duoc_xet_tn_ct2, r_g03) :- duoc_xet_tn_ct2.

%% ---------------------------------------------------------------------------
%% 17. TÍN CHỈ HỌC Ở CƠ SỞ KHÁC — Điều 12 khoản 4 điểm b (R-H01)
%% ---------------------------------------------------------------------------
vuot_tran_co_so_khac :- tc_co_so_khac(X), tc_toi_thieu_ctdt(M), 100*X > 25*M.
why(vuot_tran_co_so_khac, r_h01) :- vuot_tran_co_so_khac.

#show why/2.
#show rule_src/5.
