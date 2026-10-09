%%=============================================================================
%% elective_solver.lp — Elective & N-of-M Solver (CPA2, Tuần 8)
%%
%% Mở rộng curriculum_schema.lp với:
%%   1) Kiểu nhóm đếm môn (dem_mon) — giữ tương thích R-Formal v1.4, dùng cho
%%      CTĐT khác (K49 không có, nhưng prototype Tuần 4 từng dùng "10 chọn 2")
%%   2) Helper vị từ cho tư vấn: nhóm nào thiếu bao nhiêu, gợi ý HP còn lại
%%   3) Kiểm tra chồng nhóm và dư thừa (T3 ca biên 1 & 3 của Taxonomy Tuần 2)
%%
%% Dùng kèm: qd3266_r_formal_v1.lp + qd5339_r_formal_v1.lp
%%           + curriculum_schema.lp + curriculum_cntt_k49.lp
%%           + student facts (g10/2, diem_m/1, tich_luy/1)
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 1. NHÓM ĐẾM MÔN — "đạt ≥ N môn trong nhóm" (không dùng ở K49, giữ để tương thích)
%%    Ví dụ giả: nhom_min_mon(g_demo,2). thuoc_nhom(g_demo, C).
%% ---------------------------------------------------------------------------
mon_nhom_dat(G,X) :- nhom_kieu(G,dem_mon),
                     X = #count{ C : thuoc_nhom(G,C), tich_luy(C) }.
dat_nhom(G) :- nhom_kieu(G,dem_mon), nhom_min_mon(G,N), mon_nhom_dat(G,X), X >= N.
thieu_nhom(G,D) :- nhom_kieu(G,dem_mon), nhom_min_mon(G,N), mon_nhom_dat(G,X), X < N, D = N - X.

why(dat_nhom(G), r_a02)     :- dat_nhom(G), nhom_kieu(G,dem_mon).
why(thieu_nhom(G,D), r_a02) :- thieu_nhom(G,D), nhom_kieu(G,dem_mon).

%% ---------------------------------------------------------------------------
%% 2. HELPER CHO TƯ VẤN — liệt kê HP còn thiếu trong nhóm
%% ---------------------------------------------------------------------------
%% HP trong nhóm mà chưa tích lũy (chưa học / rớt / đang học)
hp_thieu_trong_nhom(G,C) :- thuoc_nhom(G,C), not tich_luy(C).
hp_thieu_trong_nhom(G,C) :- thuoc_nhanh(G,_,C), not tich_luy(C).

%% Mỗi nhánh thiếu bao nhiêu TC (dùng để gợi ý SV)
nhanh_thieu(G,B,D) :- nhanh(G,B), nhom_min_tc(G,N), tc_nhanh_dat(G,B,X), X < N, D = N - X.
nhanh_du(G,B)     :- dat_nhanh(G,B).

%% Nhóm điều kiện: đã đủ chưa (để phân biệt với nhóm tự chọn thường)
nhom_dieu_kien_du(G) :- nhom_dieu_kien(G), dat_nhom(G).
nhom_dieu_kien_thieu(G) :- nhom_dieu_kien(G), not dat_nhom(G).

%% Tổng hợp trạng thái nhóm cho API
nhom_trang_thai(G,du)    :- dat_nhom(G).
nhom_trang_thai(G,thieu) :- not dat_nhom(G), nhom(G).

%% ---------------------------------------------------------------------------
%% 3. KIỂM TRA CHỒNG NHÓM & DƯ THỪA (T3 ca biên 1 & 3)
%%    - Một HP không thuộc hai nhóm (đã có ràng buộc cứng ở schema, ở đây chỉ cảnh báo mềm)
%%    - Dư thừa: SV đạt nhiều hơn min trong nhóm tin_chi
%% ---------------------------------------------------------------------------
nhom_du_tc(G,X) :- nhom_kieu(G,tin_chi), dat_nhom(G), tc_nhom_dat(G,X), nhom_min_tc(G,N), X > N.
nhom_du_mon(G,X) :- nhom_kieu(G,dem_mon), dat_nhom(G), mon_nhom_dat(G,X), nhom_min_mon(G,N), X > N.

%% Cảnh báo mềm: HP thuộc nhóm nhưng dư (đã đạt nhóm mà vẫn học thêm HP cùng nhóm)
%% Không cấm, chỉ ghi nhận để Recommendation (Tuần 19) không gợi ý thừa
canh_bao_du_nhom(G,C) :- thuoc_nhom_bat_ky(G,C), tich_luy(C), nhom_du_tc(G,_).
canh_bao_du_nhom(G,C) :- thuoc_nhom_bat_ky(G,C), tich_luy(C), nhom_du_mon(G,_).

%% ---------------------------------------------------------------------------
%% 4. TỔNG HỢP ĐIỀU KIỆN TỰ CHỌN (T3) CHO Graduation
%%    dk_tu_chon đúng khi MỌI nhóm tự chọn KHÔNG phải điều kiện đều đạt
%%    (nhóm điều kiện xét riêng ở dk_hp_dieu_kien)
%%    Đã có trong qd3266_r_formal, ở đây chỉ alias để test
%% ---------------------------------------------------------------------------
dk_tu_chon_elective :- not thieu_nhom(G,_) : nhom(G), not nhom_dieu_kien(G).

%% ---------------------------------------------------------------------------
%% 5. GỢI Ý TỐI THIỂU — tập HP nhỏ nhất để lấp nhóm thiếu (dùng cho RQ3 planning)
%%    Ở chế độ kế hoạch: hoc(C) là lựa chọn, mục tiêu minimize sum TC
%% ---------------------------------------------------------------------------
#defined hoc/1.
hoc(C) :- tich_luy(C).  % ở chế độ kiểm tra thường, hoc = đã tích lũy
% Ở chế độ kế hoạch, file kiem_tra_cau_truc.lp sẽ định nghĩa lại hoc/1 là choice
