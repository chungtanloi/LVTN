%%=============================================================================
%% curriculum_schema.lp — NGỮ NGHĨA CỦA KHUNG CTĐT (CPA², Tuần 6, Curriculum KB v1)
%%
%% File này ĐỘC LẬP với ngành và khoá: nó chỉ nói nhóm tự chọn, nhánh, tiên quyết
%% theo tín chỉ nghĩa là gì. Dữ kiện cụ thể (mã HP, số TC, thành viên nhóm) nằm ở
%% curriculum_<ctdt>.lp, sinh tự động từ build_curriculum.py.
%%
%% Dùng kèm:  ../w5_rformal/qd3266_r_formal_v1.lp (cung cấp passed/1, tc_tich_luy/1)
%%            hoặc ở chế độ "kế hoạch" (kiem_tra_cau_truc.lp) nơi passed/1 là lựa chọn.
%%
%% Không có RuleId mới: mọi why/2 ở đây trỏ về R-A02 (tự chọn, Đ.7 k.3) và
%% R-A03 (tiên quyết, Đ.7 k.4) của QĐ3266 — con số và thành viên nhóm mang nguồn
%% riêng qua ctdt_src(Ma, Trang, DongTT).
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 1. THÀNH VIÊN NHÓM
%% ---------------------------------------------------------------------------
thuoc_nhom_bat_ky(G,C) :- thuoc_nhom(G,C).
thuoc_nhom_bat_ky(G,C) :- thuoc_nhanh(G,_,C).
hp_trong_nhom(C)       :- thuoc_nhom_bat_ky(_,C).

nhom_tu_chon(G) :- nhom(G).

%% Nhóm điều kiện: MỌI thành viên đều là học phần điều kiện (vd. nhóm ngoại ngữ
%% AV/PV, nhóm GDTC). Điều kiện tốt nghiệp của nhóm này thuộc Đ.32 k.1 đ.b
%% (hoàn thành học phần điều kiện), KHÔNG thuộc đ.a (đủ học phần tự chọn) —
%% phân biệt này quyết định Đ.33 k.2 (được quay lại trong 3 năm) có áp dụng không.
nhom_dieu_kien(G) :- nhom(G), thuoc_nhom_bat_ky(G,_),
                     hp_dieu_kien(C) : thuoc_nhom_bat_ky(G,C).

%% ---------------------------------------------------------------------------
%% 2. NHÓM ĐẾM TÍN CHỈ — "tích lũy ≥ N TC trong nhóm"
%% ---------------------------------------------------------------------------
tc_nhom_dat(G,X) :- nhom_kieu(G,tin_chi),
                    X = #sum{ CR,C : thuoc_nhom(G,C), tich_luy(C), course(C,CR) }.
dat_nhom(G) :- nhom_kieu(G,tin_chi), nhom_min_tc(G,N), tc_nhom_dat(G,X), X >= N.
thieu_nhom(G,D) :- nhom_kieu(G,tin_chi), nhom_min_tc(G,N), tc_nhom_dat(G,X), X < N, D = N - X.

%% ---------------------------------------------------------------------------
%% 3. NHÓM MỘT NHÁNH — "≥ N TC trong ĐÚNG MỘT nhánh" (ô "A hoặc B" của CTĐT)
%%    Tín chỉ KHÔNG cộng dồn qua nhánh: 4 TC Anh văn + 6 TC Pháp văn ≠ 10 TC ngoại ngữ.
%%    Học dư nhánh thứ hai KHÔNG bị cấm (CQ-04): chỉ không được tính cho nhóm.
%% ---------------------------------------------------------------------------
tc_nhanh_dat(G,B,X) :- nhanh(G,B),
                       X = #sum{ CR,C : thuoc_nhanh(G,B,C), tich_luy(C), course(C,CR) }.
dat_nhanh(G,B) :- nhanh(G,B), nhom_min_tc(G,N), tc_nhanh_dat(G,B,X), X >= N.
dat_nhom(G)    :- nhom_kieu(G,mot_nhanh), dat_nhanh(G,_).
thieu_nhom(G,D) :- nhom_kieu(G,mot_nhanh), nhom_min_tc(G,N), not dat_nhom(G),
                   D = #min{ N-X,B : tc_nhanh_dat(G,B,X) }.

why(dat_nhom(G), r_a02)     :- dat_nhom(G).
why(dat_nhanh(G,B), r_a02)  :- dat_nhanh(G,B).
why(thieu_nhom(G,D), r_a02) :- thieu_nhom(G,D).

%% ---------------------------------------------------------------------------
%% 4. HỌC PHẦN TỰ CHỌN "DƯ" — đạt nhưng không cần cho nhóm (Tuần 2, T3 ca biên 3)
%%    Chỉ ghi nhận; số TC của chúng vẫn vào tc_tich_luy (Đ.24 k.1 không loại trừ).
%% ---------------------------------------------------------------------------
hp_nhanh_khong_tinh(G,C) :- thuoc_nhanh(G,B,C), passed(C), dat_nhanh(G,B2), B2 != B,
                            not dat_nhanh(G,B).

%% ---------------------------------------------------------------------------
%% 4b. SV CHỌN HỌC PHẦN TỰ CHỌN ĐỂ TÍCH LŨY — CQ-06
%%     Chỉ học phần thuộc nhóm tự chọn mới được loại khỏi tích lũy.
%%     Chế độ sv_chon_tich_luy: SV CHƯA khai báo lựa chọn → hệ thống xét MỌI cách
%%     chọn. Kết luận đúng là "∃ cách chọn" trong mỗi thế giới dữ kiện, rồi "∀ thế
%%     giới" — không phải cautious trên toàn bộ answer set (xem validate I19).
%% ---------------------------------------------------------------------------
:- khong_tinh_tich_luy(C), not hp_trong_nhom(C).
{ khong_tinh_tich_luy(C) : passed(C), hp_trong_nhom(C) } :- che_do(sv_chon_tich_luy).

%% CQ-06: làm cả LVTN và TLTN không bị cấm, nhưng không nên — chỉ là khuyến nghị,
%% không phải vi phạm; nhánh Recommendation (Tuần 19) không được đề xuất cả hai.
khuyen_nghi(khong_lam_ca_lvtn_tltn) :- hinh_thuc_cuoi_khoa(A,luan_van), hinh_thuc_cuoi_khoa(B,tieu_luan),
                                      dang_ky(_,A), dang_ky(_,B).
khuyen_nghi(khong_lam_ca_lvtn_tltn) :- hinh_thuc_cuoi_khoa(A,luan_van), hinh_thuc_cuoi_khoa(B,tieu_luan),
                                      passed(A), passed(B).

%% ---------------------------------------------------------------------------
%% 5. HỌC KỲ TỔ CHỨC — dùng cho nhánh lập kế hoạch (RQ3)
%% ---------------------------------------------------------------------------
chi_mo_hk_he(C) :- mo_hk(C,3), not mo_hk(C,1), not mo_hk(C,2).

%% ---------------------------------------------------------------------------
%% 5b. KHỐI LƯỢNG HỌC PHẦN ĐIỀU KIỆN TỐI THIỂU của CTĐT (dùng cho CQ-05)
%%     = TC các HP điều kiện bắt buộc + TC tối thiểu của các nhóm điều kiện.
%% ---------------------------------------------------------------------------
tc_dk_bb(X)    :- X = #sum{ CR,C : bat_buoc(C), hp_dieu_kien(C), course(C,CR) }.
tc_dk_nhom(X)  :- X = #sum{ N,G : nhom_dieu_kien(G), nhom_min_tc(G,N) }.
tc_dk_ctdt(X)  :- tc_dk_bb(A), tc_dk_nhom(B), X = A + B.

%% ---------------------------------------------------------------------------
%% 6. RÀNG BUỘC NỘI TẠI — dòng "Cộng" của CTĐT phải khớp các dòng học phần.
%%    Chép sai một số → chương trình VÔ NGHIỆM, không im lặng cho kết quả sai.
%% ---------------------------------------------------------------------------
:- khoi(K,S,B,T), S != B + T.
:- khoi(K,_,B,_), B != #sum{ CR,C : bat_buoc(C), thuoc_khoi(C,K), course(C,CR) }.
:- khoi(K,_,_,T), T != #sum{ N,G : nhom_khoi(G,K), nhom_min_tc(G,N) }.
:- tc_toi_thieu_ctdt(T), T != #sum{ S,K : khoi(K,S,_,_) }.
:- tc_bat_buoc_ctdt(B),  B != #sum{ S,K : khoi(K,_,S,_) }.
:- tc_tu_chon_ctdt(X),   X != #sum{ S,K : khoi(K,_,_,S) }.
%% một học phần không thể vừa bắt buộc vừa thuộc nhóm, hay thuộc hai nhóm
:- bat_buoc(C), hp_trong_nhom(C).
:- thuoc_nhom_bat_ky(G1,C), thuoc_nhom_bat_ky(G2,C), G1 != G2.
:- thuoc_nhanh(G,B1,C), thuoc_nhanh(G,B2,C), B1 != B2.
