%%=============================================================================
%% recommendation.lp — chọn phương án đăng ký một học kỳ (CPA2, Tuần 19)
%%
%% Đầu vào (recommendation.py sinh, chỉ gồm ứng viên ĐÃ hợp lệ trên mọi thế giới):
%%   ung_vien(C). tc(C,CR). mo_khoa(C,N). bb(C).
%%   trong_nhom(G,C). thieu(G,D).                 nhóm tự chọn tính TC
%%   trong_nhanh(G,B,C). thieu_nhanh(G,B,D).      nhóm một nhánh (AV/PV; CN1–3)
%%   luan_van(C). tran_tc(N). can_cung_ky(C,P)   (P song hành của C, chưa học → phải chọn cùng kỳ)
%% Ràng buộc là quy chế/CTĐT; #maximize là CHÍNH SÁCH tư vấn, không phải quy chế.
%%=============================================================================
{ chon(C) } :- ung_vien(C).

%% R-C01 · QĐ3266 Đ14 k1: tối đa 20 TC một học kỳ
:- tran_tc(N), #sum{ CR,C : chon(C), tc(C,CR) } > N.

%% CTĐT: nhóm một nhánh — chỉ một nhánh
nhanh_chon(G,B) :- chon(C), trong_nhanh(G,B,C).
:- nhanh_chon(G,B1), nhanh_chon(G,B2), B1 < B2.

%% QĐ3266 Đ31: một trong ba hình thức — không cùng lúc LVTN và TLTN
:- luan_van(C1), luan_van(C2), C1 < C2, chon(C1), chon(C2).

%% Không dư nhóm: bỏ bất kỳ HP nhóm nào vẫn còn đủ thiếu hụt → HP đó thừa
:- thieu(G,D), chon(C1), trong_nhom(G,C1), tc(C1,CR1),
   S = #sum{ CR,C : chon(C), trong_nhom(G,C), tc(C,CR) }, S - CR1 >= D.
:- thieu_nhanh(G,B,D), chon(C1), trong_nhanh(G,B,C1), tc(C1,CR1),
   S = #sum{ CR,C : chon(C), trong_nhanh(G,B,C), tc(C,CR) }, S - CR1 >= D.

%% R-A04 · QĐ3266 Đ7 k5: HP song hành phải học trước hoặc học cùng lúc (chưa học → phải cùng kỳ)
:- chon(C), can_cung_ky(C,P), not chon(P).

%% Ưu tiên (chính sách): TC bắt buộc → mở khóa → TC lấp nhóm → tổng TC
#maximize { CR@5,C : chon(C), bb(C), tc(C,CR) }.
#maximize { N@4,C  : chon(C), mo_khoa(C,N) }.
#maximize { CR@2,C : chon(C), not bb(C), tc(C,CR) }.
#maximize { CR@1,C : chon(C), tc(C,CR) }.

#show chon/1.
