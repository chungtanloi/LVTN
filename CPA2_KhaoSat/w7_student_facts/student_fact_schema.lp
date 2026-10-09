%% student_fact_schema.lp — ánh xạ JSON → vị từ ASP cho CPA2 Tuần 7
%% Sinh tự động từ JSON Schema, không sửa tay.
%% Dùng kèm: qd3266_r_formal_v1.lp + qd5339_r_formal_v1.lp + curriculum_schema.lp + curriculum_cntt_k49.lp

%% Ví dụ hồ sơ sv_lvtn.json sinh:
%%   g10("CT177",75). course("CT177",3).  % tự động có từ curriculum, g10 từ hồ sơ
%%   xac_nhan_ky_luat_sach.
%%   khong_tinh_tich_luy("CT478").  % CQ-06

%% Quy ước: g10(C,X) với X = thang10 (0-100). r_b02 suy ra g4/letter.
%% passed(C) suy từ g4 >=10 hoặc diem_m(C) — không cần assert passed trực tiếp.
