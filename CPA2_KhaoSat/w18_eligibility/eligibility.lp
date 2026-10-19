%%=============================================================================
%% eligibility.lp — Eligibility module v1 (CPA2, Tuần 18)
%%
%% Đủ điều kiện (du_dk/1) cho: luận văn, tiểu luận, niên luận, niên luận cơ sở,
%% thực tập, tích lũy TC thay LVTN/TLTN, học phần thay thế.
%% Dùng kèm KB của w16 (R-Formal + CTĐT + w8/w9/w10) — tái dùng du_dk_dang_ky/1,
%% thieu_tc/2 (R-A03, QĐ3266 Điều 7 khoản 4), mien_tu/2 (R-M13), dat_nhom/1.
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 1. ĐỐI TƯỢNG XÉT ↔ HỌC PHẦN CTĐT K49 (tr.3–4)
%% ---------------------------------------------------------------------------
doi_tuong(lvtn,            "CT550E").   % Luận văn tốt nghiệp — tiên quyết ≥ 120 TC
doi_tuong(tltn,            "CT501E").   % Tiểu luận tốt nghiệp — ≥ 120 TC
doi_tuong(nien_luan,       "CT466E").   % Niên luận — ≥ 80 TC
doi_tuong(nien_luan_co_so, "CT271E").   % Niên luận cơ sở — tiên quyết CT174, CT176
doi_tuong(thuc_tap,        "CT518E").   % Thực tập doanh nghiệp — ≥ 125 TC

%% ---------------------------------------------------------------------------
%% 2. ĐIỀU KIỆN DO ĐƠN VỊ ĐÀO TẠO QUY ĐỊNH — QĐ3266 Điều 31 (tr.19), R-F04
%%    "Để được nhận đề tài LVTN hoặc TLTN, SV phải thỏa mãn các điều kiện do đơn
%%    vị đào tạo quy định." QD-12 (xác nhận ngoài văn bản, Loi 18/10/2026): điều
%%    kiện đó CHỈ là ngưỡng TC của CTĐT (≥ 120 TC) — không có điều kiện nào khác.
%%    hinh_thuc_cuoi_khoa CHỈ dùng khi có khai báo: đã công bố hình thức khác →
%%    không đủ điều kiện hình thức này (dv_cong_bo_khac). Không khai báo → không
%%    ảnh hưởng (bản trước QD-12 mở nhánh → UNKNOWN).
%% ---------------------------------------------------------------------------
can_dv_xet(lvtn).
can_dv_xet(tltn).

%% ---------------------------------------------------------------------------
%% 3. LÝ DO KHÔNG ĐỦ
%% ---------------------------------------------------------------------------
%% tiên quyết = ĐÃ TÍCH LŨY (R-A03); thieu_tc/2 đã có ở R-Formal
thieu_tien_quyet(C,P) :- doi_tuong(_,C), tien_quyet(C,P), not passed(P).
why(thieu_tien_quyet(C,P), r_a03) :- thieu_tien_quyet(C,P).

dv_cong_bo_khac(X) :- can_dv_xet(X), khai_bao(hinh_thuc), not dv_cong_bo(X).
why(dv_cong_bo_khac(X), r_f04) :- dv_cong_bo_khac(X).

%% ---------------------------------------------------------------------------
%% 4. ĐÃ HOÀN THÀNH — không báo "đủ điều kiện" cho học phần đã tích lũy
%% ---------------------------------------------------------------------------
da_hoan_thanh(X) :- doi_tuong(X,C), tich_luy(C).
da_hoan_thanh(tich_luy_tc) :- dat_nhom(g_tot_nghiep).
%% Điều 31: SV thực hiện MỘT TRONG BA hình thức → đã xong hình thức khác (hoặc nhóm
%% tốt nghiệp đã đủ) thì LVTN/TLTN không còn cần.
da_hoan_thanh(X) :- can_dv_xet(X), can_dv_xet(Y), Y != X, doi_tuong(Y,C), tich_luy(C).
da_hoan_thanh(X) :- can_dv_xet(X), dat_nhom(g_tot_nghiep).
%% HP thay thế đã đạt bằng điểm của chính nó → không cần thay thế
da_hoan_thanh(thay_the(B)) :- dang_xet(thay_the(B)), g4(B,P), P >= 10.
da_hoan_thanh(thay_the(B)) :- dang_xet(thay_the(B)), diem_m(B).

%% ---------------------------------------------------------------------------
%% 5. ĐỦ ĐIỀU KIỆN
%% ---------------------------------------------------------------------------
du_dk_ctdt(X) :- doi_tuong(X,C), du_dk_dang_ky(C).

du_dk(X) :- du_dk_ctdt(X), not dv_cong_bo_khac(X), not da_hoan_thanh(X).
why(du_dk(X), r_a03) :- du_dk(X), doi_tuong(X,_).
why(du_dk(X), r_f04) :- du_dk(X), can_dv_xet(X).

%% Điều 31 khoản 3: "SV có thể chọn hình thức không làm LVTN hoặc TLTN ... học thêm
%% các học phần tự chọn để đủ số TC" — SV tự chọn; F của LVTN/TLTN → "đăng ký làm
%% lại hoặc đăng ký các học phần thay thế".
du_dk(tich_luy_tc) :- not da_hoan_thanh(tich_luy_tc).
why(du_dk(tich_luy_tc), r_f05) :- du_dk(tich_luy_tc).

%% Học phần thay thế — QĐ5339 Điều 3 khoản 9 (R-M13) và substitutes/2 (w9)
du_dk(thay_the(B)) :- mien_tu(B,_).
du_dk(thay_the(B)) :- substitutes(A,B), passed(A).
why(du_dk(thay_the(B)), r_m13) :- du_dk(thay_the(B)).
