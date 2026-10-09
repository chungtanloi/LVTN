%%=============================================================================
%% kiem_tra_cau_truc.lp — CHẾ ĐỘ KẾ HOẠCH: "solver đọc được curriculum"
%% Nạp cùng curriculum_schema.lp + curriculum_<ctdt>.lp, KHÔNG nạp quy tắc quy chế.
%%
%% Câu hỏi: tập học phần nhỏ nhất (theo TC) thoả MỌI ràng buộc cấu trúc của CTĐT
%% là bao nhiêu TC, và có bao nhiêu tập như vậy? Nếu KB đúng thì số nhỏ nhất phải
%% bằng đúng dòng "Tổng cộng" của CTĐT — một kiểm tra mà KB không thể tự "khớp"
%% được bằng cách chép lại con số, vì nó được TÍNH từ 78 dòng và 5 nhóm.
%%=============================================================================
{ hoc(C) : course(C,_) }.
hoc(C) :- bat_buoc(C).
hoc(P) :- hoc(C), tien_quyet(C,P).          % T4a: phải tích lũy P
hoc(P) :- hoc(C), song_hanh(C,P).           % song hành: phải học P (trước/cùng lúc)
passed(C) :- hoc(C).                        % kế hoạch: coi mọi HP chọn học là đạt
tich_luy(C) :- passed(C).

:- nhom(G), not dat_nhom(G).

tong_tc(T) :- T = #sum{ CR,C : hoc(C), course(C,CR) }.
%% T4b khả thi: phần TC còn lại (trừ chính HP đó) phải đạt ngưỡng tín chỉ của nó
:- hoc(C), tien_quyet_tc(C,N), course(C,CR), tong_tc(T), T - CR < N.

#show hoc/1.
#show tong_tc/1.
