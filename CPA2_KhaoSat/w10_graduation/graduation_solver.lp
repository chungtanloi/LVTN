%%=============================================================================
%% graduation_solver.lp — Graduation Solver v1 (CPA2, Tuần 10)
%%
%% Tổng hợp T1–T7 + ngưỡng số + ba trị. Đây là file DUY NHẤT định nghĩa
%% tot_nghiep/0 từ các điều kiện thành phần — mọi KB trước chỉ định nghĩa
%% các điều kiện rời rạc (dk_*, thieu_*, canh_bao).
%%
%% Nguồn: QĐ3266 / QĐ5339 + Curriculum KB v1 + Elective/Exemption solvers
%% Dùng kèm: qd3266_r_formal_v1.lp + qd5339_r_formal_v1.lp
%%           + curriculum_schema.lp + elective_solver.lp
%%           + exemption_substitution_solver.lp + curriculum_cntt_k49.lp
%%=============================================================================

%% ---------------------------------------------------------------------------
%% 0. THẾ GIỚI MỞ CÓ KIỂM SOÁT CHO DỮ KIỆN NGOÀI (Tuần 16, sửa P15-2)
%%    Quy tắc META về cách xử lý dữ kiện THIẾU — không phải nội dung quy chế.
%%    Trước Tuần 16: thiếu dữ kiện = sai (thế giới đóng) → thiếu xác nhận kỷ luật
%%    cho tot_nghiep FALSE; thiếu da_hoc_nam2 cho "chưa quá hạn". Nay: hồ sơ KHÔNG
%%    khai báo → mở cả hai nhánh → ba trị cho UNKNOWN. Khai báo "không" thì loader
%%    phát khai_bao(ky_luat). (không kèm xac_nhan_ky_luat_sach) → FALSE thật.
%%    Biến chịu ảnh hưởng: xac_nhan_ky_luat_sach (R-F03, Đ32 k1 c);
%%    qua_thoi_gian_toi_da (R-E01/R-E02, Đ5) — qua đó thieu_dk(thoi_gian), bi_xoa_ten.
%%    khai_bao/1 chỉ được suy từ dữ kiện ĐẦU VÀO. KHÔNG viết
%%    khai_bao(ky_luat) :- xac_nhan_ky_luat_sach. — nhánh chọn "true" sẽ tự triệt
%%    tiêu điều kiện "not khai_bao" của chính nó (không ổn định) → thế giới đóng lại.
%%    Khi hồ sơ có xac_nhan_ky_luat_sach. thì lựa chọn bên dưới thừa nhưng vô hại.
%% ---------------------------------------------------------------------------
khai_bao(thoi_gian) :- da_hoc_nam2(_).
{ xac_nhan_ky_luat_sach } :- not khai_bao(ky_luat).
{ qua_thoi_gian_toi_da }  :- not khai_bao(thoi_gian).

%% ---------------------------------------------------------------------------
%% 1. BẢY ĐIỀU KIỆN THÀNH PHẦN (Taxonomy Tuần 2, T7 — đã có ở R-Formal, ở đây chỉ alias)
%% ---------------------------------------------------------------------------
%% T1 + T2/T3: bat_buoc, dat_nhom
%% T4: du_dk_dang_ky (không kiểm ở đây, chỉ khi xếp lịch)
%% T5/T6: exempted_m/recognized/substituted đã tính vào tich_luy
%% Ngưỡng số: tc_tich_luy, dtbctl, dk_hp_dieu_kien, dk_gdqp, xac_nhan_ky_luat_sach

%% dk_tin_chi: đủ TC tối thiểu CTĐT (161 ở K49)
dk_tin_chi :- tc_tich_luy(T), tc_toi_thieu_ctdt(Min), T >= Min.
why(dk_tin_chi, r_f01a) :- dk_tin_chi.

%% dk_bat_buoc: không thiếu HP bắt buộc nào
dk_bat_buoc :- not thieu_bat_buoc(_).
why(dk_bat_buoc, r_a01) :- dk_bat_buoc.

%% dk_tu_chon: mọi nhóm tự chọn KHÔNG phải điều kiện đều đạt
dk_tu_chon :- not thieu_nhom(G,_) : nhom(G), not nhom_dieu_kien(G).
why(dk_tu_chon, r_a02) :- dk_tu_chon.

%% dk_hp_dieu_kien: mọi nhóm điều kiện đạt (GDQP/GDTC/Ngoại ngữ)
%% Lưu ý: hp_dieu_kien loại gdtc/gdqp/ngoai_ngu_cb — đã có ở qd3266
has_thieu_dk_nhom :- thieu_nhom(G,_), nhom_dieu_kien(G).
has_thieu_bb_dk   :- thieu_bat_buoc(C), bat_buoc(C), hp_dieu_kien(C).
dk_hp_dieu_kien :- not has_thieu_dk_nhom, not has_thieu_bb_dk.
why(dk_hp_dieu_kien, r_f02a) :- dk_hp_dieu_kien.

%% dk_dtbctl: ĐTBCTL ≥ 2.00 (R-F01a)
dk_dtbctl :- dtbctl_ge(20).
why(dk_dtbctl, r_f01a) :- dk_dtbctl.

%% dk_gdqp: GDQP&AN ≥ 5.0 thang 10 (R-F02a) — chặt hơn D thường
dk_gdqp :- not khong_dat_gdqp(_).
why(dk_gdqp, r_f02a) :- dk_gdqp.

%% dk_ky_luat: không đang bị kỷ luật — dữ kiện ngoài, UNKNOWN nếu thiếu (mục 0)
dk_ky_luat :- xac_nhan_ky_luat_sach.
why(dk_ky_luat, r_f03) :- dk_ky_luat.
truc_ky_luat_khong_co_du_lieu :- not xac_nhan_ky_luat_sach.

%% dk_thoi_gian: không quá hạn (R-E01, R-F09)
dk_thoi_gian :- not qua_thoi_gian_toi_da.
why(dk_thoi_gian, r_e01) :- dk_thoi_gian.

%% ---------------------------------------------------------------------------
%% 2. ĐIỀU KIỆN TỐT NGHIỆP TỔNG HỢP — 7 thành phần
%%    cond_discipline (R-F03) luôn cần xac_nhan_ky_luat_sach → ba trị tự nhiên
%% ---------------------------------------------------------------------------
du_dk_hoc_vu :- dk_tin_chi, dk_bat_buoc, dk_tu_chon, dk_hp_dieu_kien, dk_dtbctl, dk_gdqp, dk_thoi_gian.
why(du_dk_hoc_vu, r_f01a) :- du_dk_hoc_vu.

%% Tuần 16 (P16-2): dk_thoi_gian đặt ở đây, vì du_dk_hoc_vu còn được R-Formal định
%% nghĩa KHÔNG có thời gian (hai định nghĩa hợp lại) → đặt trong du_dk_hoc_vu không chặn được.
tot_nghiep :- du_dk_hoc_vu, dk_ky_luat, dk_thoi_gian.
why(tot_nghiep, r_f01a) :- du_dk_hoc_vu.
why(tot_nghiep, r_f03)  :- dk_ky_luat.
why(tot_nghiep, r_e01)  :- dk_thoi_gian.

%% Helper: liệt kê điều kiện nào còn thiếu (để Verbalizer diễn đạt)
thieu_dk(tin_chi)      :- not dk_tin_chi.
thieu_dk(bat_buoc)     :- not dk_bat_buoc.
thieu_dk(tu_chon)      :- not dk_tu_chon.
thieu_dk(hp_dieu_kien) :- not dk_hp_dieu_kien.
thieu_dk(dtbctl)       :- not dk_dtbctl.
thieu_dk(gdqp)         :- not dk_gdqp.
thieu_dk(ky_luat)      :- not dk_ky_luat.
thieu_dk(thoi_gian)    :- not dk_thoi_gian.

why(thieu_dk(tin_chi), r_f01a)      :- thieu_dk(tin_chi).
why(thieu_dk(bat_buoc), r_a01)      :- thieu_dk(bat_buoc).
why(thieu_dk(tu_chon), r_a02)       :- thieu_dk(tu_chon).
why(thieu_dk(hp_dieu_kien), r_f02a) :- thieu_dk(hp_dieu_kien).
why(thieu_dk(dtbctl), r_f01a)       :- thieu_dk(dtbctl).
why(thieu_dk(gdqp), r_f02a)         :- thieu_dk(gdqp).
why(thieu_dk(ky_luat), r_f03)       :- thieu_dk(ky_luat).
why(thieu_dk(thoi_gian), r_e01)     :- thieu_dk(thoi_gian).

%% ---------------------------------------------------------------------------
%% 3. TIÊN QUYẾT CHO ĐĂNG KÝ — T4a/T4b/T4c
%%    Đã có ở qd3266: du_dk_dang_ky/1, thieu_tc/2, vi_pham_song_hanh/2
%%    Ở đây chỉ helper để liệt kê HP nào chưa đủ ĐK đăng ký
%% ---------------------------------------------------------------------------
hp_chua_du_dk(C) :- course(C,_), not du_dk_dang_ky(C).
why(hp_chua_du_dk(C), r_a03) :- hp_chua_du_dk(C).

%% ---------------------------------------------------------------------------
%% 4. XẾP HẠNG TỐT NGHIỆP — R-F06/F07 (ĐTBCTL + vượt 5% F)
%%    Đã có ở qd3266: hang_goc, vuot_5_phan_tram, hang_cuoi
%% ---------------------------------------------------------------------------

%% ---------------------------------------------------------------------------
%% 5. BA TRỊ CHO TỐT NGHIỆP — không cần code thêm, đã có ở validate
%%    TRUE  = tot_nghiep trong mọi answer set
%%    FALSE = tot_nghiep trong không answer set nào
%%    UNKNOWN = còn lại (ví dụ thiếu một nhóm, hoặc thiếu xac_nhan_ky_luat_sach)
%% ---------------------------------------------------------------------------
