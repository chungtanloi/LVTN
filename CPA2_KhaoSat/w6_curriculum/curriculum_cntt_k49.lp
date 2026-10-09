%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% curriculum_cntt_k49.lp — SINH TỰ ĐỘNG bởi build_curriculum.py. KHÔNG SỬA TAY.
%% Nguồn: QĐ 2423/QĐ-ĐHCT ngày 05/6/2023 — CTĐT ngành Công nghệ thông tin
%%        LVTN/NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf — mục 6, trang 3–4
%% Dùng kèm: curriculum_schema.lp (ngữ nghĩa nhóm, độc lập ngành/khoá)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ctdt(cntt_k49).  nganh_ma("7480201").  danh_hieu(ky_su).
van_ban_ctdt(qd2423_ctdt).

%% --- Thời gian đào tạo 4,5 năm → QĐ3266 Điều 5: tối đa 9 năm (18 nửa năm) ---
thiet_ke_nam2(9).
khoa_tu_k45. khoa_tu_k47. khoa_den_k49.

%% --- Dòng 'Cộng' của CTĐT, chép riêng để kiểm tra chéo với từng dòng ---------
tc_toi_thieu_ctdt(161).  tc_bat_buoc_ctdt(125).  tc_tu_chon_ctdt(36).
khoi(dai_cuong, 56, 41, 15).
khoi(co_so_nganh, 46, 46, 0).
khoi(chuyen_nganh, 59, 38, 21).

%% --- Nhóm tự chọn ----------------------------------------------------------
nhom(g_gdtc).  nhom_kieu(g_gdtc,tin_chi).  nhom_min_tc(g_gdtc,3).  nhom_khoi(g_gdtc,dai_cuong).
nhom(g_ngoai_ngu).  nhom_kieu(g_ngoai_ngu,mot_nhanh).  nhom_min_tc(g_ngoai_ngu,10).  nhom_khoi(g_ngoai_ngu,dai_cuong).
nhanh(g_ngoai_ngu,av).  thuoc_nhanh(g_ngoai_ngu,av,"XH023"). thuoc_nhanh(g_ngoai_ngu,av,"XH024"). thuoc_nhanh(g_ngoai_ngu,av,"XH025"). thuoc_nhanh(g_ngoai_ngu,av,"XH031"). thuoc_nhanh(g_ngoai_ngu,av,"XH032"). thuoc_nhanh(g_ngoai_ngu,av,"XH033").
nhanh(g_ngoai_ngu,pv).  thuoc_nhanh(g_ngoai_ngu,pv,"FL001"). thuoc_nhanh(g_ngoai_ngu,pv,"FL002"). thuoc_nhanh(g_ngoai_ngu,pv,"FL003"). thuoc_nhanh(g_ngoai_ngu,pv,"FL007"). thuoc_nhanh(g_ngoai_ngu,pv,"FL008"). thuoc_nhanh(g_ngoai_ngu,pv,"FL009").
nhom(g_xa_hoi).  nhom_kieu(g_xa_hoi,tin_chi).  nhom_min_tc(g_xa_hoi,2).  nhom_khoi(g_xa_hoi,dai_cuong).
nhom(g_chuyen_nganh).  nhom_kieu(g_chuyen_nganh,mot_nhanh).  nhom_min_tc(g_chuyen_nganh,6).  nhom_khoi(g_chuyen_nganh,chuyen_nganh).
nhanh(g_chuyen_nganh,cn1).  thuoc_nhanh(g_chuyen_nganh,cn1,"CT211"). thuoc_nhanh(g_chuyen_nganh,cn1,"CT297").
nhanh(g_chuyen_nganh,cn2).  thuoc_nhanh(g_chuyen_nganh,cn2,"CT449"). thuoc_nhanh(g_chuyen_nganh,cn2,"CT484").
nhanh(g_chuyen_nganh,cn3).  thuoc_nhanh(g_chuyen_nganh,cn3,"CT522"). thuoc_nhanh(g_chuyen_nganh,cn3,"CT279").
nhom(g_tot_nghiep).  nhom_kieu(g_tot_nghiep,tin_chi).  nhom_min_tc(g_tot_nghiep,15).  nhom_khoi(g_tot_nghiep,chuyen_nganh).

%% --- Học phần: course/2, ten/2, thuoc_khoi/2, ctdt_src/3 --------------------
course("QP010E",2). ten("QP010E","Giáo dục quốc phòng và An ninh 1"). thuoc_khoi("QP010E",dai_cuong). ctdt_src("QP010E",3,1). bat_buoc("QP010E"). loai_hp("QP010E",gdqp). mo_hk_bo_tri_rieng("QP010E").
course("QP011E",2). ten("QP011E","Giáo dục quốc phòng và An ninh 2"). thuoc_khoi("QP011E",dai_cuong). ctdt_src("QP011E",3,2). bat_buoc("QP011E"). loai_hp("QP011E",gdqp). mo_hk_bo_tri_rieng("QP011E").
course("QP012",2). ten("QP012","Giáo dục quốc phòng và An ninh 3"). thuoc_khoi("QP012",dai_cuong). ctdt_src("QP012",3,3). bat_buoc("QP012"). loai_hp("QP012",gdqp). mo_hk_bo_tri_rieng("QP012").
course("QP013",2). ten("QP013","Giáo dục quốc phòng và An ninh 4"). thuoc_khoi("QP013",dai_cuong). ctdt_src("QP013",3,4). bat_buoc("QP013"). loai_hp("QP013",gdqp). mo_hk_bo_tri_rieng("QP013").
course("TC100",3). ten("TC100","Giáo dục thể chất 1+2+3"). thuoc_khoi("TC100",dai_cuong). ctdt_src("TC100",3,5). thuoc_nhom(g_gdtc,"TC100"). loai_hp("TC100",gdtc). mo_hk("TC100",1). mo_hk("TC100",2). mo_hk("TC100",3).
course("XH023",4). ten("XH023","Anh văn căn bản 1"). thuoc_khoi("XH023",dai_cuong). ctdt_src("XH023",3,6). loai_hp("XH023",ngoai_ngu_cb). ngon_ngu_hp("XH023",anh). mo_hk("XH023",1). mo_hk("XH023",2). mo_hk("XH023",3).
course("XH024",3). ten("XH024","Anh văn căn bản 2"). thuoc_khoi("XH024",dai_cuong). ctdt_src("XH024",3,7). loai_hp("XH024",ngoai_ngu_cb). ngon_ngu_hp("XH024",anh). song_hanh("XH024","XH023"). mo_hk("XH024",1). mo_hk("XH024",2). mo_hk("XH024",3).
course("XH025",3). ten("XH025","Anh văn căn bản 3"). thuoc_khoi("XH025",dai_cuong). ctdt_src("XH025",3,8). loai_hp("XH025",ngoai_ngu_cb). ngon_ngu_hp("XH025",anh). song_hanh("XH025","XH024"). mo_hk("XH025",1). mo_hk("XH025",2). mo_hk("XH025",3).
course("XH031",4). ten("XH031","Anh văn tăng cường 1"). thuoc_khoi("XH031",dai_cuong). ctdt_src("XH031",3,9). loai_hp("XH031",ngoai_ngu_cb). ngon_ngu_hp("XH031",anh). song_hanh("XH031","XH025"). mo_hk("XH031",1). mo_hk("XH031",2). mo_hk("XH031",3).
course("XH032",3). ten("XH032","Anh văn tăng cường 2"). thuoc_khoi("XH032",dai_cuong). ctdt_src("XH032",3,10). loai_hp("XH032",ngoai_ngu_cb). ngon_ngu_hp("XH032",anh). song_hanh("XH032","XH031"). mo_hk("XH032",1). mo_hk("XH032",2). mo_hk("XH032",3).
course("XH033",3). ten("XH033","Anh văn tăng cường 3"). thuoc_khoi("XH033",dai_cuong). ctdt_src("XH033",3,11). loai_hp("XH033",ngoai_ngu_cb). ngon_ngu_hp("XH033",anh). song_hanh("XH033","XH032"). mo_hk("XH033",1). mo_hk("XH033",2). mo_hk("XH033",3).
course("FL001",4). ten("FL001","Pháp văn căn bản 1"). thuoc_khoi("FL001",dai_cuong). ctdt_src("FL001",3,12). loai_hp("FL001",ngoai_ngu_cb). ngon_ngu_hp("FL001",phap). mo_hk("FL001",1). mo_hk("FL001",2). mo_hk("FL001",3).
course("FL002",3). ten("FL002","Pháp văn căn bản 2"). thuoc_khoi("FL002",dai_cuong). ctdt_src("FL002",3,13). loai_hp("FL002",ngoai_ngu_cb). ngon_ngu_hp("FL002",phap). song_hanh("FL002","FL001"). mo_hk("FL002",1). mo_hk("FL002",2). mo_hk("FL002",3).
course("FL003",3). ten("FL003","Pháp văn căn bản 3"). thuoc_khoi("FL003",dai_cuong). ctdt_src("FL003",3,14). loai_hp("FL003",ngoai_ngu_cb). ngon_ngu_hp("FL003",phap). song_hanh("FL003","FL002"). mo_hk("FL003",1). mo_hk("FL003",2). mo_hk("FL003",3).
course("FL007",4). ten("FL007","Pháp văn tăng cường 1"). thuoc_khoi("FL007",dai_cuong). ctdt_src("FL007",3,15). loai_hp("FL007",ngoai_ngu_cb). ngon_ngu_hp("FL007",phap). song_hanh("FL007","FL003"). mo_hk("FL007",1). mo_hk("FL007",2). mo_hk("FL007",3).
course("FL008",3). ten("FL008","Pháp văn tăng cường 2"). thuoc_khoi("FL008",dai_cuong). ctdt_src("FL008",3,16). loai_hp("FL008",ngoai_ngu_cb). ngon_ngu_hp("FL008",phap). song_hanh("FL008","FL007"). mo_hk("FL008",1). mo_hk("FL008",2). mo_hk("FL008",3).
course("FL009",3). ten("FL009","Pháp văn tăng cường 3"). thuoc_khoi("FL009",dai_cuong). ctdt_src("FL009",3,17). loai_hp("FL009",ngoai_ngu_cb). ngon_ngu_hp("FL009",phap). song_hanh("FL009","FL008"). mo_hk("FL009",1). mo_hk("FL009",2). mo_hk("FL009",3).
course("ML014",3). ten("ML014","Triết học Mác - Lênin"). thuoc_khoi("ML014",dai_cuong). ctdt_src("ML014",3,18). bat_buoc("ML014"). mo_hk("ML014",1). mo_hk("ML014",2). mo_hk("ML014",3).
course("ML016",2). ten("ML016","Kinh tế chính trị Mác - Lênin"). thuoc_khoi("ML016",dai_cuong). ctdt_src("ML016",3,19). bat_buoc("ML016"). tien_quyet("ML016","ML014"). mo_hk("ML016",1). mo_hk("ML016",2). mo_hk("ML016",3).
course("ML018",2). ten("ML018","Chủ nghĩa xã hội khoa học"). thuoc_khoi("ML018",dai_cuong). ctdt_src("ML018",3,20). bat_buoc("ML018"). tien_quyet("ML018","ML016"). mo_hk("ML018",1). mo_hk("ML018",2). mo_hk("ML018",3).
course("ML019",2). ten("ML019","Lịch sử Đảng Cộng sản Việt Nam"). thuoc_khoi("ML019",dai_cuong). ctdt_src("ML019",3,21). bat_buoc("ML019"). tien_quyet("ML019","ML018"). mo_hk("ML019",1). mo_hk("ML019",2). mo_hk("ML019",3).
course("ML021",2). ten("ML021","Tư tưởng Hồ Chí Minh"). thuoc_khoi("ML021",dai_cuong). ctdt_src("ML021",3,22). bat_buoc("ML021"). tien_quyet("ML021","ML019"). mo_hk("ML021",1). mo_hk("ML021",2). mo_hk("ML021",3).
course("KL001E",2). ten("KL001E","Pháp luật đại cương"). thuoc_khoi("KL001E",dai_cuong). ctdt_src("KL001E",3,23). bat_buoc("KL001E"). mo_hk("KL001E",1). mo_hk("KL001E",2). mo_hk("KL001E",3).
course("ML007",2). ten("ML007","Logic học đại cương"). thuoc_khoi("ML007",dai_cuong). ctdt_src("ML007",3,24). thuoc_nhom(g_xa_hoi,"ML007"). mo_hk("ML007",1). mo_hk("ML007",2). mo_hk("ML007",3).
course("XH028",2). ten("XH028","Xã hội học đại cương"). thuoc_khoi("XH028",dai_cuong). ctdt_src("XH028",3,25). thuoc_nhom(g_xa_hoi,"XH028"). mo_hk("XH028",1). mo_hk("XH028",2). mo_hk("XH028",3).
course("XH011",2). ten("XH011","Cơ sở văn hóa Việt Nam"). thuoc_khoi("XH011",dai_cuong). ctdt_src("XH011",3,26). thuoc_nhom(g_xa_hoi,"XH011"). mo_hk("XH011",1). mo_hk("XH011",2). mo_hk("XH011",3).
course("XH012",2). ten("XH012","Tiếng Việt thực hành"). thuoc_khoi("XH012",dai_cuong). ctdt_src("XH012",3,27). thuoc_nhom(g_xa_hoi,"XH012"). mo_hk("XH012",1). mo_hk("XH012",2). mo_hk("XH012",3).
course("XH014",2). ten("XH014","Văn bản và lưu trữ học đại cương"). thuoc_khoi("XH014",dai_cuong). ctdt_src("XH014",3,28). thuoc_nhom(g_xa_hoi,"XH014"). mo_hk("XH014",1). mo_hk("XH014",2). mo_hk("XH014",3).
course("KN001E",2). ten("KN001E","Kỹ năng mềm"). thuoc_khoi("KN001E",dai_cuong). ctdt_src("KN001E",3,29). thuoc_nhom(g_xa_hoi,"KN001E"). mo_hk("KN001E",1). mo_hk("KN001E",2). mo_hk("KN001E",3).
course("KN002E",2). ten("KN002E","Đổi mới sáng tạo và khởi nghiệp"). thuoc_khoi("KN002E",dai_cuong). ctdt_src("KN002E",3,30). thuoc_nhom(g_xa_hoi,"KN002E"). mo_hk("KN002E",1). mo_hk("KN002E",2). mo_hk("KN002E",3).
course("TN001",3). ten("TN001","Vi - Tích phân A1"). thuoc_khoi("TN001",dai_cuong). ctdt_src("TN001",3,31). bat_buoc("TN001"). mo_hk("TN001",1). mo_hk("TN001",2). mo_hk("TN001",3).
course("TN002",4). ten("TN002","Vi - Tích phân A2"). thuoc_khoi("TN002",dai_cuong). ctdt_src("TN002",3,32). bat_buoc("TN002"). tien_quyet("TN002","TN001"). mo_hk("TN002",1). mo_hk("TN002",2). mo_hk("TN002",3).
course("TN010",3). ten("TN010","Xác suất thống kê"). thuoc_khoi("TN010",dai_cuong). ctdt_src("TN010",3,33). bat_buoc("TN010"). mo_hk("TN010",1). mo_hk("TN010",2). mo_hk("TN010",3).
course("TN012",4). ten("TN012","Đại số tuyến tính và Hình học"). thuoc_khoi("TN012",dai_cuong). ctdt_src("TN012",3,34). bat_buoc("TN012"). mo_hk("TN012",1). mo_hk("TN012",2). mo_hk("TN012",3).
course("CT100",2). ten("CT100","Kỹ năng học đại học"). thuoc_khoi("CT100",dai_cuong). ctdt_src("CT100",3,35). bat_buoc("CT100"). mo_hk("CT100",1). mo_hk("CT100",2). mo_hk("CT100",3).
course("CT200",4). ten("CT200","Nền tảng công nghệ thông tin"). thuoc_khoi("CT200",dai_cuong). ctdt_src("CT200",3,36). bat_buoc("CT200"). mo_hk("CT200",1). mo_hk("CT200",2). mo_hk("CT200",3).
course("CT101",4). ten("CT101","Lập trình căn bản A"). thuoc_khoi("CT101",co_so_nganh). ctdt_src("CT101",3,37). bat_buoc("CT101"). mo_hk("CT101",1). mo_hk("CT101",2).
course("CT177",3). ten("CT177","Cấu trúc dữ liệu"). thuoc_khoi("CT177",co_so_nganh). ctdt_src("CT177",3,38). bat_buoc("CT177"). tien_quyet("CT177","CT101"). mo_hk("CT177",1). mo_hk("CT177",2).
course("CT174",3). ten("CT174","Phân tích và thiết kế thuật toán"). thuoc_khoi("CT174",co_so_nganh). ctdt_src("CT174",3,39). bat_buoc("CT174"). tien_quyet("CT174","CT177"). mo_hk("CT174",1). mo_hk("CT174",2).
course("CT172",4). ten("CT172","Toán rời rạc"). thuoc_khoi("CT172",co_so_nganh). ctdt_src("CT172",3,40). bat_buoc("CT172"). mo_hk("CT172",1). mo_hk("CT172",2).
course("CT175",3). ten("CT175","Lý thuyết đồ thị"). thuoc_khoi("CT175",co_so_nganh). ctdt_src("CT175",3,41). bat_buoc("CT175"). tien_quyet("CT175","CT177"). mo_hk("CT175",1). mo_hk("CT175",2).
course("CT190",2). ten("CT190","Nhập môn trí tuệ nhân tạo"). thuoc_khoi("CT190",co_so_nganh). ctdt_src("CT190",4,42). bat_buoc("CT190"). mo_hk("CT190",1). mo_hk("CT190",2).
course("CT180",3). ten("CT180","Cơ sở dữ liệu"). thuoc_khoi("CT180",co_so_nganh). ctdt_src("CT180",4,43). bat_buoc("CT180"). tien_quyet("CT180","CT177"). mo_hk("CT180",1). mo_hk("CT180",2).
course("CT182",3). ten("CT182","Ngôn ngữ mô hình hóa"). thuoc_khoi("CT182",co_so_nganh). ctdt_src("CT182",4,44). bat_buoc("CT182"). tien_quyet("CT182","CT176"). song_hanh("CT182","CT180"). mo_hk("CT182",1). mo_hk("CT182",2).
course("CT296",3). ten("CT296","Phân tích và thiết kế hệ thống thông tin"). thuoc_khoi("CT296",co_so_nganh). ctdt_src("CT296",4,45). bat_buoc("CT296"). tien_quyet("CT296","CT180"). mo_hk("CT296",1). mo_hk("CT296",2).
course("CT173",3). ten("CT173","Kiến trúc máy tính"). thuoc_khoi("CT173",co_so_nganh). ctdt_src("CT173",4,46). bat_buoc("CT173"). mo_hk("CT173",1). mo_hk("CT173",2).
course("CT178",3). ten("CT178","Nguyên lý hệ điều hành"). thuoc_khoi("CT178",co_so_nganh). ctdt_src("CT178",4,47). bat_buoc("CT178"). tien_quyet("CT178","CT173"). mo_hk("CT178",1). mo_hk("CT178",2).
course("CT112",3). ten("CT112","Mạng máy tính"). thuoc_khoi("CT112",co_so_nganh). ctdt_src("CT112",4,48). bat_buoc("CT112"). tien_quyet("CT112","CT178"). mo_hk("CT112",1). mo_hk("CT112",2).
course("CT176",3). ten("CT176","Lập trình hướng đối tượng"). thuoc_khoi("CT176",co_so_nganh). ctdt_src("CT176",4,49). bat_buoc("CT176"). tien_quyet("CT176","CT101"). mo_hk("CT176",1). mo_hk("CT176",2).
course("CT179",3). ten("CT179","Quản trị hệ thống"). thuoc_khoi("CT179",co_so_nganh). ctdt_src("CT179",4,50). bat_buoc("CT179"). mo_hk("CT179",1). mo_hk("CT179",2).
course("CT188",3). ten("CT188","Nhập môn lập trình web"). thuoc_khoi("CT188",co_so_nganh). ctdt_src("CT188",4,51). bat_buoc("CT188"). mo_hk("CT188",1). mo_hk("CT188",2).
course("CT271E",3). ten("CT271E","Niên luận cơ sở - CNTT"). thuoc_khoi("CT271E",chuyen_nganh). ctdt_src("CT271E",4,52). bat_buoc("CT271E"). tien_quyet("CT271E","CT174"). tien_quyet("CT271E","CT176"). mo_hk("CT271E",1). mo_hk("CT271E",2).
course("CT273",3). ten("CT273","Giao diện người - máy"). thuoc_khoi("CT273",chuyen_nganh). ctdt_src("CT273",4,53). bat_buoc("CT273"). mo_hk("CT273",1). mo_hk("CT273",2).
course("CT294",3). ten("CT294","Máy học ứng dụng"). thuoc_khoi("CT294",chuyen_nganh). ctdt_src("CT294",4,54). bat_buoc("CT294"). mo_hk("CT294",1). mo_hk("CT294",2).
course("CT202",3). ten("CT202","Nguyên lý máy học"). thuoc_khoi("CT202",chuyen_nganh). ctdt_src("CT202",4,55). bat_buoc("CT202"). mo_hk("CT202",1). mo_hk("CT202",2).
course("CT467",3). ten("CT467","Quản trị dữ liệu"). thuoc_khoi("CT467",chuyen_nganh). ctdt_src("CT467",4,56). bat_buoc("CT467"). tien_quyet("CT467","CT180"). mo_hk("CT467",1). mo_hk("CT467",2).
course("CT293",3). ten("CT293","Mạng và truyền thông dữ liệu"). thuoc_khoi("CT293",chuyen_nganh). ctdt_src("CT293",4,57). bat_buoc("CT293"). tien_quyet("CT293","CT112"). mo_hk("CT293",1). mo_hk("CT293",2).
course("CT275",3). ten("CT275","Công nghệ Web"). thuoc_khoi("CT275",chuyen_nganh). ctdt_src("CT275",4,58). bat_buoc("CT275"). tien_quyet("CT275","CT188"). mo_hk("CT275",1). mo_hk("CT275",2).
course("CT300",3). ten("CT300","Phát triển phần mềm"). thuoc_khoi("CT300",chuyen_nganh). ctdt_src("CT300",4,59). bat_buoc("CT300"). tien_quyet("CT300","CT176"). mo_hk("CT300",1). mo_hk("CT300",2).
course("CT223",3). ten("CT223","Quản lý dự án phần mềm"). thuoc_khoi("CT223",chuyen_nganh). ctdt_src("CT223",4,60). bat_buoc("CT223"). mo_hk("CT223",1). mo_hk("CT223",2).
course("CT222",3). ten("CT222","An toàn hệ thống"). thuoc_khoi("CT222",chuyen_nganh). ctdt_src("CT222",4,61). bat_buoc("CT222"). mo_hk("CT222",1). mo_hk("CT222",2).
course("CT211",3). ten("CT211","An ninh mạng"). thuoc_khoi("CT211",chuyen_nganh). ctdt_src("CT211",4,62). mo_hk("CT211",1). mo_hk("CT211",2).
course("CT297",3). ten("CT297","Pháp y máy tính"). thuoc_khoi("CT297",chuyen_nganh). ctdt_src("CT297",4,63). mo_hk("CT297",1). mo_hk("CT297",2).
course("CT449",3). ten("CT449","Phát triển ứng dụng Web"). thuoc_khoi("CT449",chuyen_nganh). ctdt_src("CT449",4,64). mo_hk("CT449",1). mo_hk("CT449",2).
course("CT484",3). ten("CT484","Phát triển ứng dụng di động"). thuoc_khoi("CT484",chuyen_nganh). ctdt_src("CT484",4,65). mo_hk("CT484",1). mo_hk("CT484",2).
course("CT522",3). ten("CT522","Nền tảng về internet vạn vật"). thuoc_khoi("CT522",chuyen_nganh). ctdt_src("CT522",4,66). mo_hk("CT522",1). mo_hk("CT522",2).
course("CT279",3). ten("CT279","Blockchain"). thuoc_khoi("CT279",chuyen_nganh). ctdt_src("CT279",4,67). mo_hk("CT279",1). mo_hk("CT279",2).
course("CT466E",3). ten("CT466E","Niên luận - CNTT"). thuoc_khoi("CT466E",chuyen_nganh). ctdt_src("CT466E",4,68). bat_buoc("CT466E"). tien_quyet_tc("CT466E",80). mo_hk("CT466E",1). mo_hk("CT466E",2).
course("CT518E",5). ten("CT518E","Thực tập doanh nghiệp - CNTT"). thuoc_khoi("CT518E",chuyen_nganh). ctdt_src("CT518E",4,69). bat_buoc("CT518E"). tien_quyet_tc("CT518E",125). mo_hk("CT518E",3).
course("CT550E",15). ten("CT550E","Luận văn tốt nghiệp - CNTT"). thuoc_khoi("CT550E",chuyen_nganh). ctdt_src("CT550E",4,70). thuoc_nhom(g_tot_nghiep,"CT550E"). tien_quyet_tc("CT550E",120). mo_hk("CT550E",1). mo_hk("CT550E",2).
course("CT501E",6). ten("CT501E","Tiểu luận tốt nghiệp - CNTT"). thuoc_khoi("CT501E",chuyen_nganh). ctdt_src("CT501E",4,71). thuoc_nhom(g_tot_nghiep,"CT501E"). tien_quyet_tc("CT501E",120). mo_hk("CT501E",1). mo_hk("CT501E",2).
course("CT478",3). ten("CT478","Trung tâm dữ liệu"). thuoc_khoi("CT478",chuyen_nganh). ctdt_src("CT478",4,72). thuoc_nhom(g_tot_nghiep,"CT478"). mo_hk("CT478",1). mo_hk("CT478",2).
course("CT283",3). ten("CT283","Hệ thống chịu lỗi"). thuoc_khoi("CT283",chuyen_nganh). ctdt_src("CT283",4,73). thuoc_nhom(g_tot_nghiep,"CT283"). mo_hk("CT283",1). mo_hk("CT283",2).
course("CT233",3). ten("CT233","Điện toán đám mây"). thuoc_khoi("CT233",chuyen_nganh). ctdt_src("CT233",4,74). thuoc_nhom(g_tot_nghiep,"CT233"). mo_hk("CT233",1). mo_hk("CT233",2).
course("CT482",3). ten("CT482","Xử lý dữ liệu lớn"). thuoc_khoi("CT482",chuyen_nganh). ctdt_src("CT482",4,75). thuoc_nhom(g_tot_nghiep,"CT482"). mo_hk("CT482",1). mo_hk("CT482",2).
course("CT210",3). ten("CT210","Thị giác máy tính"). thuoc_khoi("CT210",chuyen_nganh). ctdt_src("CT210",4,76). thuoc_nhom(g_tot_nghiep,"CT210"). mo_hk("CT210",1). mo_hk("CT210",2).
course("CT219",3). ten("CT219","Xử lý ngôn ngữ tự nhiên"). thuoc_khoi("CT219",chuyen_nganh). ctdt_src("CT219",4,77). thuoc_nhom(g_tot_nghiep,"CT219"). mo_hk("CT219",1). mo_hk("CT219",2).
course("CT312",3). ten("CT312","Khai khoáng dữ liệu"). thuoc_khoi("CT312",chuyen_nganh). ctdt_src("CT312",4,78). thuoc_nhom(g_tot_nghiep,"CT312"). mo_hk("CT312",1). mo_hk("CT312",2).

%% --- Hình thức cuối khoá (QĐ3266 Điều 31) -----------------------------------
hinh_thuc_cuoi_khoa("CT550E", luan_van).  hinh_thuc_cuoi_khoa("CT501E", tieu_luan).

%% --- TÊN GỌI TƯƠNG THÍCH với ctdt_cntt_k49.lp của Tuần 5 (ca C34–C36) --------
chon_cn(B)          :- dat_nhanh(g_chuyen_nganh,B).
dat_nhom_cn         :- dat_nhom(g_chuyen_nganh).
nhieu_hon_mot_cn    :- dat_nhanh(g_chuyen_nganh,B1), dat_nhanh(g_chuyen_nganh,B2), B1 != B2.
du_dk_tin_chi_lam_lvtn :- du_dk_tc("CT550E").
chi_mo_hk(C,K)      :- mo_hk(C,K), not mo_hk(C,K2) : mo_hk(C,K2), K2 != K.
