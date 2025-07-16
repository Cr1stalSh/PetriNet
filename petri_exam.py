import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext
from graphviz import Digraph
from PIL import Image, ImageTk
import random

class Place:
    def __init__(self, name, tokens=0):
        self.name = name
        self.tokens = tokens

class Transition:
    def __init__(self, name, pre, post):
        self.name = name
        self.pre = pre
        self.post = post

    def enabled(self, marking):
        return all(marking[p] >= cnt for p, cnt in self.pre.items())

    def fire(self, marking):
        if not self.enabled(marking):
            return None
        new_marking = marking.copy()
        for p, cnt in self.pre.items():
            new_marking[p] -= cnt
        for p, cnt in self.post.items():
            new_marking[p] += cnt
        return new_marking

class PetriNetGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Petri Net: Extended Exam Model (Graphviz)')
        self.root.geometry('1000x550')

        self.img_label = tk.Label(self.root)
        self.img_label.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        # Кнопки
        btn_step = tk.Button(btn_frame, text='Шаг', command=self.step,
                             font=('Arial', 12, 'bold'), bg='#008CBA', fg='white',
                             activebackground='#007bb5', relief='raised', bd=2,
                             padx=12, pady=6)
        btn_step.grid(row=0, column=0, padx=5)

        btn_reset = tk.Button(btn_frame, text='Сброс', command=self.reset,
                              font=('Arial', 12), bg='#f44336', fg='white',
                              activebackground='#d32f2f', relief='raised', bd=2,
                              padx=12, pady=6)
        btn_reset.grid(row=0, column=1, padx=5)

        btn_tree = tk.Button(btn_frame, text='Дерево достижимости', command=self.show_reachability_tree,
                             font=('Arial', 12), bg='#008CBA', fg='white',
                             activebackground='#007bb5', relief='raised', bd=2,
                             padx=12, pady=6)
        btn_tree.grid(row=0, column=2, padx=5)

        btn_matrix = tk.Button(btn_frame, text='Матрица достижимости', command=self.show_reachability_matrix,
                               font=('Arial', 12), bg='#008CBA', fg='white',
                               activebackground='#007bb5', relief='raised', bd=2,
                               padx=12, pady=6)
        btn_matrix.grid(row=0, column=3, padx=5)

        # Определение мест и переходов
        self.places = {
            'Waiting': Place('Waiting', tokens=4),
            'FreeExaminer': Place('FreeExaminer', tokens=1),
            'Preparing': Place('Preparing', tokens=0),
            'InExam': Place('InExam', tokens=0),
            'Done': Place('Done', tokens=0)
        }
        self.initial_marking = {p: self.places[p].tokens for p in self.places}

        self.transitions = [
            Transition('TTckt', pre={'Waiting': 1, 'FreeExaminer': 1}, post={'Preparing': 1, 'FreeExaminer': 1}),
            Transition('StEx', pre={'Preparing': 1, 'FreeExaminer': 1}, post={'InExam': 1}),
            Transition('EndEx', pre={'InExam': 1}, post={'Done': 1, 'FreeExaminer': 1}),
            Transition('ReEx', pre={'InExam': 1}, post={'Preparing': 1, 'FreeExaminer': 1})
        ]

        self.dot = Digraph(format='png')
        self.dot.attr('graph', rankdir='LR')
        self.dot.attr('node', shape='circle', fixedsize='true', width='1.2', style='filled', fillcolor='lightblue')
        self.dot.attr('edge', fontsize='10')

        self._render_and_display()
        self.root.mainloop()

    def reset(self):
        # Сброс разметки к начальной
        for p, tokens in self.initial_marking.items():
            self.places[p].tokens = tokens
        self._render_and_display()

    def _build_graph(self):
        self.dot.clear()
        self.dot.attr('graph', rankdir='LR')
        self.dot.attr('node', shape='circle', fixedsize='true', width='1.2', style='filled', fillcolor='lightblue')
        self.dot.attr('edge', fontsize='10')

        for pname, place in self.places.items():
            dots = ' '.join(['●'] * place.tokens)
            label = f'<{pname}<BR/><FONT POINT-SIZE="16">{dots}</FONT>>' if dots else pname
            self.dot.node(pname, label=label)

        for t in self.transitions:
            vlabel = '<' + '<BR/>'.join(list(t.name)) + '>'
            self.dot.node(t.name, label=vlabel, shape='box', fixedsize='true', width='0.6', height='1.5', style='filled', fillcolor='gray', fontcolor='white')
            for p, cnt in t.pre.items():
                self.dot.edge(p, t.name, label=str(cnt) if cnt>1 else '')
            for p, cnt in t.post.items():
                self.dot.edge(t.name, p, label=str(cnt) if cnt>1 else '')

    def _render_and_display(self):
        self._build_graph()
        fname = 'petri_net_extended'
        self.dot.render(fname, cleanup=True)
        img = Image.open(f'{fname}.png')
        self.photo = ImageTk.PhotoImage(img)
        self.img_label.config(image=self.photo)

    def step(self):
        current = {p: self.places[p].tokens for p in self.places}
        # 1. Выдача билета
        give = next(t for t in self.transitions if t.name == 'TTckt')
        if give.enabled(current):
            self._apply_marking(give.fire(current))
            return
        # 2. Начало экзамена
        stex = next(t for t in self.transitions if t.name == 'StEx')
        if stex.enabled(current) and current['InExam'] == 0:
            self._apply_marking(stex.fire(current))
            return
        # 3. Если в экзамене, выбор с весами: EndEx 70%, ReEx 30%
        if current['InExam'] > 0:
            end = next(t for t in self.transitions if t.name == 'EndEx')
            rex = next(t for t in self.transitions if t.name == 'ReEx')
            choices = []
            weights = []
            if end.enabled(current):
                choices.append(end)
                weights.append(0.7)
            if rex.enabled(current):
                choices.append(rex)
                weights.append(0.3)
            if choices:
                t = random.choices(choices, weights)[0]
                self._apply_marking(t.fire(current))
                return
        # 4. Завершение, если нет вариантов
        messagebox.showinfo('Done', 'Сеть выполнена')

    def _apply_marking(self, new):
        for p in self.places:
            self.places[p].tokens = new[p]
        self._render_and_display()

    def marking_to_str(self, m):
        return f"W:{m['Waiting']}, Pr:{m['Preparing']}, F:{m['FreeExaminer']}, I:{m['InExam']}, D:{m['Done']}"

    def compute_reachability_set(self):
        order, visited, queue = [], set(), [self.initial_marking.copy()]
        keys = list(self.places.keys())
        while queue:
            cur = queue.pop(0)
            key = tuple(cur[p] for p in keys)
            if key in visited:
                continue
            visited.add(key)
            order.append(cur.copy())
            for t in self.transitions:
                if t.enabled(cur):
                    queue.append(t.fire(cur))
        return order

    def show_reachability_tree(self):
        nodes = [('root', self.marking_to_str(self.initial_marking))]
        edges = []
        self._build_tree(self.initial_marking, 0, 10, 'root', nodes, edges)
        tree = Digraph(format='png')
        tree.attr('graph', rankdir='TB')
        tree.attr('node', shape='box', style='filled', fillcolor='lightyellow')
        tree.attr('edge', fontsize='10')
        for nid, label in nodes:
            tree.node(nid, label=label)
        for s, d, t in edges:
            tree.edge(s, d, label=t)
        tree.render('reach_tree_ext', cleanup=True)
        win = Toplevel(self.root)
        win.title('Дерево достижимости')
        img = ImageTk.PhotoImage(Image.open('reach_tree_ext.png'))
        lbl = tk.Label(win, image=img)
        lbl.image = img
        lbl.pack(fill=tk.BOTH, expand=True)

    def show_reachability_matrix(self):
        marks = self.compute_reachability_set()
        keys = list(self.places.keys())
        idx = {tuple(m[p] for p in keys): i for i, m in enumerate(marks)}
        hdr = 'Idx | Marking'.ljust(35) + ''.join(f"| {t.name.center(12)} " for t in self.transitions) + '\n' + '-'*(35+len(self.transitions)*14) + '\n'
        rows = ''
        for i, m in enumerate(marks):
            rows += f"{i:>3} | {self.marking_to_str(m):<30}"
            for t in self.transitions:
                if t.enabled(m):
                    new = t.fire(m)
                    j = idx[tuple(new[p] for p in keys)]
                    rows += f"| {j:^12} "
                else:
                    rows += f"| {'-':^12} "
            rows += '\n'
        win = Toplevel(self.root)
        win.title('Матрица достижимости')
        ta = scrolledtext.ScrolledText(win, width=100, height=20, font=('Courier', 12))
        ta.pack(fill=tk.BOTH, expand=True)
        ta.insert(tk.END, hdr + rows)
        ta.config(state=tk.DISABLED)

    def _build_tree(self, cur, d, md, nid, nodes, edges):
        if d >= md:
            return
        for t in self.transitions:
            if not t.enabled(cur):
                continue
            nm = t.fire(cur)
            cid = f"{nid}.{t.name}"
            nodes.append((cid, self.marking_to_str(nm)))
            edges.append((nid, cid, t.name))
            self._build_tree(nm, d+1, md, cid, nodes, edges)

if __name__ == '__main__':
    PetriNetGUI()
