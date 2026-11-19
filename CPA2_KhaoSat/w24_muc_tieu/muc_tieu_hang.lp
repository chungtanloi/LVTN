%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% muc_tieu_hang.lp — MỤC TIÊU HẠNG TỐT NGHIỆP (CPA2, Tuần 24)
%%
%% Câu hỏi: "cần trung bình bao nhiêu (ở X tín chỉ) để tốt nghiệp ÍT NHẤT loại H?"
%% Đây là PHÉP TÍNH trên định nghĩa đã hình thức hoá, không phải dự đoán và không thêm quy định mới:
%%   ĐTBCTL = tl_tu / tl_mau (R-B10; tl_tu là điểm thang 4 ×10 nhân TC) · ngưỡng hạng hang(H,L), L ×100,
%%   so hữu tỉ theo cận dưới (R-F06, QD-14) · hạ một mức hạng xuất sắc/giỏi (R-F07/R-F07b → ha_mot_muc).
%%   Đạt "ít nhất H" sau khi học thêm X TC với tổng điểm S (cùng thang với tl_tu):
%%       10·(N + S) ≥ L·(D + X)   ⇔   S ≥ ⌈(L·(D + X) − 10·N) / 10⌉
%%   L chia hết cho 10 nên phép chia đúng, không làm tròn. Mỗi học phần đạt cho S từ 10·TC (D) đến 40·TC (A).
%%
%% Giả định (ghi trong câu trả lời): đạt MỌI học phần sắp học (F không vào ĐTBCTL và không tích lũy TC);
%% không tính học cải thiện điểm; X mặc định = số TC TỐI THIỂU còn phải tích lũy có tính điểm =
%% tc_toi_thieu_ctdt − tc_dk_ctdt − tc_tl_khong_dk (CQ-05: 161 TC gồm 21 TC học phần điều kiện,
%% học phần điều kiện không vào ĐTBCTL).
%%
%% Dùng kèm: R-Formal (qd3266 + qd5339), CTĐT, graduation_solver (nhánh mở hạ bậc khi chưa khai báo).
%% Đầu vào: muc_tieu_hang(H).  Tuỳ chọn: tc_du_kien(X) (số TC sẽ học, do câu hỏi nêu).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#defined muc_tieu_hang/1.
#defined tc_du_kien/1.
#defined ha_mot_muc/0.

%% --- Số TC sẽ học (X) --------------------------------------------------------
co_tc_du_kien :- tc_du_kien(_).
tc_con_lai(R) :- tc_toi_thieu_ctdt(M), tc_dk_ctdt(K), tc_tl_khong_dk(T), R = M - K - T, R > 0.
tc_con_lai(0) :- tc_toi_thieu_ctdt(M), tc_dk_ctdt(K), tc_tl_khong_dk(T), M - K - T <= 0.
tc_xet(X) :- tc_du_kien(X).
tc_xet(R) :- tc_con_lai(R), not co_tc_du_kien.

%% --- Ngưỡng hiệu lực cho "ít nhất H" (R-F06 + R-F07) -------------------------
%% Không bị hạ: L = cận dưới của H. Bị hạ một mức (chỉ xuất sắc, giỏi): ít nhất giỏi cần HẠNG GỐC xuất sắc;
%% xuất sắc không đạt được; khá / trung bình không đổi (giỏi gốc bị hạ vẫn là khá).
mt_ha :- ha_mot_muc.
nguong_mt(H,L) :- muc_tieu_hang(H), hang(H,L), not mt_ha.
nguong_mt(H,L) :- muc_tieu_hang(H), hang(H,L), mt_ha, H != gioi, H != xuat_sac.
nguong_mt(gioi,L) :- muc_tieu_hang(gioi), mt_ha, hang(xuat_sac,L).
mt_khong_the(xuat_sac,ha_bac) :- muc_tieu_hang(xuat_sac), mt_ha.

%% --- Tổng điểm tối thiểu S trên X TC -----------------------------------------
mt_v(H,V,X) :- nguong_mt(H,L), tl_tu(N), tl_mau(D), tc_xet(X), V = L*(D+X) - 10*N.
mt_s(H,S,X) :- mt_v(H,V,X), V > 0, S = (V+9)/10.
mt_s(H,0,X) :- mt_v(H,V,X), V <= 0.

mt_da_dat(H)           :- mt_s(H,0,0), tl_mau(D), D > 0.            % X = 0, ĐTBCTL hiện tại đã đạt (review M1:
                                                                    % D = 0 → chưa có ĐTBCTL, không phải "đã đạt")
mt_khong_the(H,het_tc) :- mt_s(H,S,0), S > 0.                       % X = 0, chưa đạt, không còn TC tối thiểu
mt_chi_can_qua(H)      :- mt_s(H,S,X), X > 0, S <= 10*X.            % mọi HP đạt D là đủ
mt_khong_the(H,diem)   :- mt_s(H,S,X), X > 0, S > 40*X.             % toàn A vẫn không đủ
mt_can(H,S,X)          :- mt_s(H,S,X), X > 0, S > 10*X, S <= 40*X.

mt_kha_thi(H) :- mt_can(H,_,_).
mt_kha_thi(H) :- mt_chi_can_qua(H).
mt_kha_thi(H) :- mt_da_dat(H).

%% --- Chứng chỉ: chỉ trỏ quy tắc đã có (R-B10, R-F06, R-F07) -------------------
mt_kq(mt_can(H,S,X))          :- mt_can(H,S,X).
mt_kq(mt_chi_can_qua(H))      :- mt_chi_can_qua(H).
mt_kq(mt_da_dat(H))           :- mt_da_dat(H).
mt_kq(mt_khong_the(H,diem))   :- mt_khong_the(H,diem).
mt_kq(mt_khong_the(H,het_tc)) :- mt_khong_the(H,het_tc).
why(K, r_b10) :- mt_kq(K).
why(K, r_f06) :- mt_kq(K).
why(K, r_f07) :- mt_kq(K), mt_ha, muc_tieu_hang(gioi).
why(mt_khong_the(xuat_sac,ha_bac), r_f07) :- mt_khong_the(xuat_sac,ha_bac).
