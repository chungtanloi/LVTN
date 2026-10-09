%%=============================================================================
%% exemption_substitution_solver.lp — Exemption & Substitution Solver (CPA2, Tuần 9)
%%
%% Mục tiêu Tuần 9: "Phân biệt passed / exempted_M / recognized / substituted"
%%
%% File này TÍCH HỢP các quy tắc đã có từ qd3266/qd5339 với CTĐT và nhóm N-of-M,
%% bổ sung:
%%   1) Phân biệt kế toán T5: exempted_M (M, không vào ĐTBCTL) vs recognized (có vào)
%%   2) Thay thế T6: substitutes/2 + substituted/1, xử lý chênh lệch tín chỉ (QD-10)
%%   3) Helper cho tư vấn: nhóm đạt nhờ miễn/thay thế, con trỏ nguồn why/2
%%
%% Dùng kèm: qd3266_r_formal_v1.lp + qd5339_r_formal_v1.lp (đã có diem_m/exempted_m/
%%           recognized/mien_treo/bac_ngoai_ngu/du_dk_xin_mien/duoc_mien/g4_chuyen)
%%           + curriculum_schema.lp + elective_solver.lp + curriculum_cntt_k49.lp
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 1. PHÂN BIỆT KẾ TOÁN T5 — đã có trong qd5339, ở đây chỉ alias + helper
%% ---------------------------------------------------------------------------
%% exempted_m(C)  : HP điều kiện miễn bằng chứng chỉ → điểm M → vào TC, KHÔNG vào ĐTBCTL
%% recognized(C)  : công nhận điểm từ CTĐT đã học        → vào TC VÀ vào ĐTBCTL (§3 k.11)
%% passed(C) đã suy từ cả hai (qd3266 r_b03/r_b04 + qd5339 r_m05/r_m04)
%%
%% Helper: HP đạt nhờ miễn/thay thế (để báo cáo trong chứng chỉ)
hp_dat_nho_mien(C)    :- exempted_m(C).
hp_dat_nho_cong_nhan(C) :- recognized(C).

why(hp_dat_nho_mien(C), r_m05)    :- hp_dat_nho_mien(C).
why(hp_dat_nho_cong_nhan(C), r_m15) :- hp_dat_nho_cong_nhan(C).

%% Nhóm đạt nhờ miễn: đếm cả HP miễn vào tc_nhom_dat (qua tich_luy)
%% đã tự động vì tich_luy(C) :- passed(C) và passed suy từ diem_m/recognized
nhom_dat_nho_mien(G) :- nhom(G), dat_nhom(G),
                        #count{ C : thuoc_nhom_bat_ky(G,C), exempted_m(C) } >= 1.
nhom_dat_nho_cong_nhan(G) :- nhom(G), dat_nhom(G),
                             #count{ C : thuoc_nhom_bat_ky(G,C), recognized(C) } >= 1.

%% ---------------------------------------------------------------------------
%% 2. THAY THẾ T6 — substitutes/2
%% ---------------------------------------------------------------------------
%% Dữ kiện: substitutes(HP_Thay_The, HP_Bi_Thay). Ví dụ:
%%   substitutes("CT271E","CT201E").  % niên luận chuyển ngành
%%   substitutes("CT172","CT172E").   % đổi mã giữa các khoá
%%   substitutes("ML009","ML014").    % QĐ5339 Đ3 k.9 (ML009 2TC → ML014 3TC)
%%
%% Quy tắc: nếu A được dùng thay B và A đã đạt thì B coi như đạt.
%% Chênh lệch tín chỉ: TC tính theo HP ĐƯỢC MIỄN (B), điểm tính theo trung bình
%% có trọng số của các HP đã học (QD-10, R-M04) — đã có ở qd5339.

%% HP được thay thế coi như đạt (substituted)
substituted(B) :- substitutes(A,B), passed(A).
why(substituted(B), r_m13) :- substituted(B), substitutes(A,B), passed(A).
%% cũng có thể r_h02 (tham_quyen) cho trường hợp "tương đương" do Tổ Xét miễn quyết

passed(B) :- substituted(B).
why(passed(B), r_m13) :- substituted(B).

%% ML thay thế qua mien_tu (QĐ5339 Đ3 k.9) cũng coi như thay thế
substituted(B) :- mien_tu(B,A), passed(A).
passed(B) :- mien_tu(B,A), passed(A).
why(substituted(B), r_m13) :- substituted(B), mien_tu(B,_).
why(passed(B), r_m13) :- mien_tu(B,A), passed(A).

%% Không cho dùng một HP thay cho hai HP khác nhau cùng lúc (nếu KB định nghĩa 1-n)
:- substitutes(A,B1), substitutes(A,B2), B1 != B2, substituted(B1), substituted(B2), not cho_phep_thay_mot_nhieu(A).

%% Mặc định cho phép thay một→nhiều chỉ với ML010 (QĐ5339 Đ3 k.9: ML010 → ML016+ML018)
cho_phep_thay_mot_nhieu("ML010").

%% Helper: HP thay thế được dùng
hp_thay_the(A,B) :- substitutes(A,B), substituted(B), passed(A).

%% ---------------------------------------------------------------------------
%% 3. ĐỔI MÃ GIỮA CÁC KHOÁ — CODE_ALIASES (Tuần 2, T1 ca biên)
%%    CT172 ↔ CT172E, CT190 ↔ CT190E. Về mặt KB là thay thế hai chiều.
%% ---------------------------------------------------------------------------
substitutes("CT172","CT172E"). substitutes("CT172E","CT172").
substitutes("CT190","CT190E"). substitutes("CT190E","CT190").
substitutes("CT101","CT101E"). substitutes("CT101E","CT101").

%% ---------------------------------------------------------------------------
%% 4. LUẬN VĂN ↔ HỌC PHẦN THAY THẾ — KHÔNG phải T6 ở K49 (Tuần 6 phát hiện)
%%    CT550E (LVTN 15), CT501E (TLTN 6) và 7 HP 3 TC nằm chung ô "15 TC"
%%    → ràng buộc là đủ 15 TC trong nhóm g_tot_nghiep (kiểu tin_chi), không phải
%%    quan hệ thay thế 1-1. Ở đây chỉ ghi helper để giải thích cho SV:
%% ---------------------------------------------------------------------------
hinh_thuc_tot_nghiep(luan_van)  :- tich_luy("CT550E").
hinh_thuc_tot_nghiep(tieu_luan) :- tich_luy("CT501E").
hinh_thuc_tot_nghiep(hp_le)     :- dat_nhom(g_tot_nghiep), not tich_luy("CT550E"), not tich_luy("CT501E").

why(hinh_thuc_tot_nghiep(luan_van), r_f05)  :- hinh_thuc_tot_nghiep(luan_van).
why(hinh_thuc_tot_nghiep(tieu_luan), r_f05) :- hinh_thuc_tot_nghiep(tieu_luan).
why(hinh_thuc_tot_nghiep(hp_le), r_f05)     :- hinh_thuc_tot_nghiep(hp_le).

%% ---------------------------------------------------------------------------
%% 5. TỔNG HỢP TRẠNG THÁI HỌC PHẦN — 7 trạng thái Trục C (Tuần 2)
%%    Dùng để trả lời "HP này ở trạng thái nào?" mà không nhầm.
%% ---------------------------------------------------------------------------
%% Ưu tiên alias: nếu C là HP gốc đã passed trực tiếp (có g10/diem_m), thì vẫn là passed
%% chỉ khi C chỉ đạt nhờ substituted/mien_tu thì mới là substituted
trang_thai_hp(C, passed)      :- passed(C), g10(C,_), not exempted_m(C), not recognized(C).
trang_thai_hp(C, passed)      :- passed(C), diem_m(C), not exempted_m(C).  % M trực tiếp
trang_thai_hp(C, exempted_M)  :- exempted_m(C).
trang_thai_hp(C, recognized)  :- recognized(C).
trang_thai_hp(C, substituted) :- substituted(C), not exempted_m(C), not recognized(C), not g10(C,_), not diem_m(C).
trang_thai_hp(C, failed)      :- g4(C,0), not passed(C).  % F
trang_thai_hp(C, in_progress) :- dang_hoc(C).
trang_thai_hp(C, unknown)     :- course(C,_), not passed(C), not g4(C,_), not diem_m(C), not diem_w(C), not diem_i(C), not dang_hoc(C).

%% Độ ưu tiên khi một HP có nhiều nhãn (ví dụ vừa exempted_M vừa substituted): lấy nhãn gốc
%% Thứ tự: exempted_M > recognized > substituted > passed
%% (đã đảm bảo bằng not ở trên)

%% ---------------------------------------------------------------------------
%% 6. CHÊNH LỆCH TÍN CHỈ KHI THAY THẾ — QD-10 (R-M04)
%%    Đã có ở qd5339: g4 tính theo trung bình có trọng số, TC tính theo HP ĐƯỢC MIỄN.
%%    Ở đây chỉ helper để kiểm tra: HP thay thế có TC khác HP bị thay?
%% ---------------------------------------------------------------------------
chenh_lech_tc(A,B,DA) :- substitutes(A,B), course(A,CA), course(B,CB), CA != CB, DA = CB - CA.
chenh_lech_tc(A,B,DA) :- ml_thay(A,B), course(A,CA), course(B,CB), CA != CB, DA = CB - CA.
why(chenh_lech_tc(A,B,DA), r_m04) :- chenh_lech_tc(A,B,DA).
