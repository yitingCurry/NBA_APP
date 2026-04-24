from nba_app.constants import COLORS
from nba_app.constants import DIFFICULTY_FILES
import tkinter as tk
from nba_app.helpFunction import resource_path
from PIL import ImageTk, Image
import random
from tkinter import messagebox

current_quiz_difficulty = None

def set_quiz_difficulty(level, diff_easy_btn=None, diff_med_btn=None, diff_hard_btn=None, quiz_frame=None, current_mode=None):
    global current_quiz_difficulty
    current_quiz_difficulty = level
    try:
        for name, btn in (('easy', diff_easy_btn), ('medium', diff_med_btn), ('hard', diff_hard_btn)):
            if btn is None:
                continue
            if name == level:
                btn.config(bg=COLORS['accent'])
            else:
                btn.config(bg=COLORS['menu_item'])
    except Exception:
        pass
    try:
        if current_mode == "quiz" and quiz_frame is not None and quiz_frame.winfo_ismapped():
            build_embedded_quiz(quiz_frame)
    except Exception:
        pass


def load_quiz_from_txt(path):
    qbank = []
    try:
        with open(path, encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith('#'):
                    continue
                parts = [p.strip() for p in ln.split('|')]
                if len(parts) < 6:
                    continue
                q = parts[0]
                opts = parts[1:5]
                try:
                    a = int(parts[5])
                    if a < 0 or a > 3:
                        a = 0
                except Exception:
                    a = 0
                qbank.append({'q': q, 'opts': opts, 'a': a})
    except Exception as e:
        print(f"載入題庫失敗: {e}")
    return qbank


def build_embedded_quiz(parent):
    # clear
    for w in parent.winfo_children():
        try:
            w.destroy()
        except Exception:
            pass

    parent._built = True
    parent.config(bg=COLORS['card_bg'])

    # local canvas + content frame
    scrollbar_quiz = tk.Scrollbar(parent, orient="vertical", bg=COLORS['secondary_bg'], troughcolor=COLORS['card_bg'])
    scrollbar_quiz.pack(side="right", fill="y")
    canvas = tk.Canvas(parent, bg=COLORS['card_bg'], highlightthickness=0, yscrollcommand=scrollbar_quiz.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar_quiz.config(command=canvas.yview)
    content = tk.Frame(canvas, bg=COLORS['card_bg'])
    window = canvas.create_window((0, 0), window=content, anchor="nw")

    def on_config(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
    def on_canvas(e):
        canvas.itemconfig(window, width=e.width)
    content.bind('<Configure>', on_config)
    canvas.bind('<Configure>', on_canvas)

    def on_mouse(e):
        canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
    canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', on_mouse))
    canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

    if current_quiz_difficulty is None:
        lbl = tk.Label(content, text="請在左側選擇題目難度（簡單 / 中等 / 困難）後開始小遊戲。",
                       font=("微軟正黑體", 14), bg=COLORS['card_bg'], fg=COLORS['text_dim'], wraplength=760, justify='center', pady=40)
        lbl.pack(expand=True)
        return

    quiz_file = resource_path(DIFFICULTY_FILES.get(current_quiz_difficulty, 'quiz_medium.txt'))
    qbank = load_quiz_from_txt(quiz_file)

    # dedupe
    try:
        seen = set(); uq = []
        for it in qbank:
            k = str(it.get('q','')).strip()
            if k and k not in seen:
                seen.add(k); uq.append(it)
        qbank = uq
    except Exception:
        pass

    random.shuffle(qbank)
    try:
        if len(qbank) > 10:
            qbank = random.sample(qbank, 10)
    except Exception:
        pass

    total = len(qbank)
    idx = 0
    submitted = False
    answers = [tk.IntVar(value=-1) for _ in range(total)]
    wrong_indices = []
    wrong_labels = {}

    title = tk.Label(content, text='NBA 小遊戲：選擇題', font=("微軟正黑體", 28, 'bold'), bg=COLORS['card_bg'], fg=COLORS['accent'])
    title.pack(anchor='nw', padx=20, pady=12)

    # photos (optional)
    try:
        photos = tk.Frame(content, bg=COLORS['card_bg'])
        photos.place(relx=1.0, rely=0, anchor='ne', x=-20, y=20)
        p1 = resource_path('kal.jpg')
        im1 = Image.open(p1).resize((200,350)); ph1 = ImageTk.PhotoImage(im1)
        l1 = tk.Label(photos, image=ph1, bg=COLORS['card_bg']); l1.image = ph1
        p2 = resource_path('william.jpg')
        im2 = Image.open(p2).resize((200,350)); ph2 = ImageTk.PhotoImage(im2)
        l2 = tk.Label(photos, image=ph2, bg=COLORS['card_bg']); l2.image = ph2
        l1.grid(row=0,column=0); l2.grid(row=0,column=1)

        big_lbl = tk.Label(photos, text = "勇士總冠軍😁", bg = COLORS['card_bg'], fg = "yellow", font=("Impact", 28, "bold"))
        # 用 grid 排列
        l1.grid(row=0, column=0, padx=3)
        l2.grid(row=0, column=1, padx=3)
        big_lbl.grid(row=1, column=0, columnspan=2, pady=10)  # 跨兩個 column，置中
    except Exception:
        pass

    qlabel = tk.Label(content, text='', font=("微軟正黑體",20), bg=COLORS['card_bg'], fg=COLORS['text'], wraplength=650, justify='left')
    qlabel.pack(anchor='nw', padx=20, pady=(6,12))

    opts_frame = tk.Frame(content, bg=COLORS['card_bg'])
    opts_frame.pack(padx=20, anchor='w')
    rbs = []
    for i in range(4):
        rb = tk.Radiobutton(opts_frame, text='', variable=tk.IntVar(value=-1), value=i, font=("微軟正黑體",18),
                            bg=COLORS['card_bg'], fg=COLORS['text'], selectcolor=COLORS['secondary_bg'], anchor='w', justify='left')
        rb.pack(fill='x', pady=6, anchor='w')
        rbs.append(rb)

    status = tk.Label(content, text='', bg=COLORS['card_bg'], fg=COLORS['text_dim'])
    status.pack(anchor='w', padx=20, pady=(6,0))
    
    # use two labels so we can color the lines differently (wrong=red, correct=green)
    compare_frame = tk.Frame(content, bg=COLORS['card_bg'])
    compare_wrong = tk.Label(compare_frame, text='', font=("微軟正黑體",16,'bold'), bg=COLORS['card_bg'], fg='red', justify='left', anchor='w')
    compare_correct = tk.Label(compare_frame, text='', font=("微軟正黑體",16,'bold'), bg=COLORS['card_bg'], fg='green', justify='left', anchor='w')
    compare_frame.pack_forget()

    feedback = tk.Label(content, text='', font=("微軟正黑體",20,'bold'), bg=COLORS['card_bg'], fg=COLORS['accent'])
    feedback.pack_forget()

    def update_wrong_highlights(ci):
        for qidx, lbl in wrong_labels.items():
            lbl.config(bg=COLORS['accent'] if qidx==ci else COLORS['secondary_bg'], fg='white' if qidx==ci else COLORS['text'])

    def load_question(i):
        nonlocal rbs, qlabel, status, compare_frame, answers, submitted
        qlabel.config(text=f"{i+1}. {qbank[i]['q']}")
        # show compare frame (it contains two stacked labels) and place it directly after the status label
        try:
            compare_frame.pack(after=status, anchor='w', padx=20, pady=(0,0))
        except Exception:
            compare_frame.pack(anchor='w', padx=20, pady=(0,0))
            
        for j, rb in enumerate(rbs):
            rb.config(text=qbank[i]['opts'][j], variable=answers[i], value=j)
            if submitted:
                correct = qbank[i]['a']; user = answers[i].get()
                if j==correct:
                    rb.config(fg='yellow', font=("微軟正黑體",18,'bold'))
                elif j==user and user!=correct:
                    rb.config(fg='white', font=("微軟正黑體",18,'bold'))
                else:
                    rb.config(fg=COLORS['text'], font=("微軟正黑體",18))
            else:
                rb.config(state='normal', fg=COLORS['text'], font=("微軟正黑體",18))
        if submitted:
            user = answers[i].get(); correct = qbank[i]['a']
            user_text = qbank[i]['opts'][user] if 0<=user<len(qbank[i]['opts']) else '未作答'
            correct_text = qbank[i]['opts'][correct]
            # clear both first
            compare_wrong.pack_forget(); compare_correct.pack_forget()
            if user==correct:
                compare_correct.config(text=f"✅ 正確答案：{correct_text}")
                compare_correct.pack(anchor='w')
            else:
                compare_wrong.config(text=f"❌ 你的答案：{user_text}")
                compare_correct.config(text=f"✅ 正確答案：{correct_text}")
                compare_wrong.pack(anchor='w')
                compare_correct.pack(anchor='w')
                if i in wrong_indices:
                    update_wrong_highlights(i)
        else:
            # hide compare frame when not submitted
            try:
                compare_frame.pack_forget()
            except Exception:
                pass
        status.config(text=f"題目 {i+1} / {total}")
        canvas.yview_moveto(0)
        try:
            prev_btn.config(state='normal' if i>0 else 'disabled')
            next_btn.config(state='normal' if i<total-1 else 'disabled')
        except Exception:
            pass

    def go_prev():
        nonlocal idx
        if idx>0:
            idx-=1; load_question(idx)
    def go_next():
        nonlocal idx
        if idx<total-1:
            idx+=1; load_question(idx)

    def submit_all():
        nonlocal submitted, wrong_indices, wrong_labels
        unanswered = [i+1 for i,v in enumerate(answers) if v.get()==-1]
        if unanswered:
            ok = messagebox.askyesno('未完成題目', f"尚有題目未作答：{unanswered}\n確定要送出並以未答題視為錯誤嗎？", parent=parent)
            if not ok:
                return
        submitted=True; score=0; wrong_indices=[]
        for i,q in enumerate(qbank):
            user = answers[i].get(); correct = q['a']
            if user==correct: score+=1
            else: wrong_indices.append(i)
        messagebox.showinfo('結果', f'你得到 {score} / {total} 分！', parent=parent)
        if score>=8: base_msg='評語：你肯定在NBA裡混了很久，太強了啦，勇士總冠軍😁'
        elif 3<=score<=7: base_msg='評語：還不錯啦，多看勇士比賽就會拿到更高的分數喔，勇士總冠軍😎'
        else: base_msg='評語：你沒救了，勇士總冠軍🥺'
        if not wrong_indices:
            feedback.pack(anchor='w', padx=20); feedback.config(text=f"🎉 全部答對，恭喜！\n\n{base_msg}")
        else:
            details = tk.Frame(content, bg=COLORS['card_bg']); details.pack(anchor='w', padx=20, pady=(20,0), fill='x')
            tk.Label(details, text='❌ 錯題明細（點擊可跳轉查看）：', font=("微軟正黑體",14,'bold'), bg=COLORS['card_bg'], fg=COLORS['accent']).pack(anchor='w', pady=(0,5))
            for i in wrong_indices[:10]:
                user = answers[i].get(); correct = qbank[i]['a']
                user_text = qbank[i]['opts'][user] if 0<=user<len(qbank[i]['opts']) else '未作答'
                correct_text = qbank[i]['opts'][correct]
                txt = f"第{i+1}題：你的答案：{user_text}  |  正確答案：{correct_text}"
                lbl = tk.Label(details, text=txt, font=("微軟正黑體",12), bg=COLORS['secondary_bg'], fg=COLORS['text'], cursor='hand2', padx=10, pady=5, anchor='w')
                lbl.pack(fill='x', pady=2)
                wrong_labels[i]=lbl
                lbl.bind('<Button-1>', lambda e, qi=i: (globals().get('jump_to_question') and globals()['jump_to_question'](qi)))
                lbl.bind('<Enter>', lambda e, l=lbl: l.config(bg=COLORS['menu_item_hover']))
                lbl.bind('<Leave>', lambda e, l=lbl, qi=i: l.config(bg=COLORS['accent'] if qi==idx else COLORS['secondary_bg']))
            feedback.pack(anchor='w', padx=20); feedback.config(text=base_msg)
        try:
            btn_frame.destroy()
        except Exception:
            pass
        load_question(idx)
        try:
            content.update_idletasks(); canvas.configure(scrollregion=canvas.bbox('all'))
        except Exception:
            pass

    def jump_to_question_local(qi):
        nonlocal idx
        idx = qi; load_question(idx)

    globals()['jump_to_question'] = jump_to_question_local

    load_question(0)

    btn_frame = tk.Frame(content, bg=COLORS['card_bg']); btn_frame.pack(anchor='w', padx=20, pady=20)
    prev_btn = tk.Button(btn_frame, text='上一題', command=go_prev, bg=COLORS['menu_item'], fg=COLORS['text']); prev_btn.pack(side='left', padx=6)
    next_btn = tk.Button(btn_frame, text='下一題', command=go_next, bg=COLORS['menu_item'], fg=COLORS['text']); next_btn.pack(side='left', padx=6)
    submit_btn = tk.Button(btn_frame, text='送出全部', command=submit_all, bg=COLORS['button'], fg='white'); submit_btn.pack(side='left', padx=12)

    try:
        content.update_idletasks(); canvas.configure(scrollregion=canvas.bbox('all'))
    except Exception:
        pass
