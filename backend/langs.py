"""Language support layer.
Python and JavaScript run on JSON test data directly. Java and C++ need typed code, so we infer the argument and
return types from the test cases (int, bool, str, list of ints, list of list of ints) and generate starter code
plus a test harness automatically."""
import ast

LANGS = {"python": "Python", "javascript": "JavaScript", "java": "Java", "cpp": "C++"}
INT_MAX = 2**31 - 1
RESERVED = {"int", "long", "short", "byte", "char", "double", "float", "boolean", "bool", "void", "new", "class", "this",
            "super", "default", "switch", "case", "do", "for", "while", "if", "else", "return", "static", "public", "private",
            "protected", "final", "string", "vector", "main", "auto", "template", "typename", "namespace", "using", "delete",
            "union", "struct", "enum", "const", "goto", "try", "catch", "throw", "import", "package", "interface", "var",
            "let", "function", "typeof", "in", "of", "null", "true", "false"}

def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool) and abs(x) <= INT_MAX

def _tag(v):
    if isinstance(v, bool): return "bool"
    if _is_int(v): return "int"
    if isinstance(v, str): return "str" if all(c >= " " for c in v) else None
    if isinstance(v, list):
        if all(_is_int(x) for x in v): return "ints"
        if all(isinstance(x, list) and all(_is_int(y) for y in x) for x in v): return "matrix"
    return None

def _merge(tags, values):
    s = set(tags)
    if None in s: return None
    if len(s) == 1: return tags[0]
    if s == {"ints", "matrix"} and all(v == [] for t, v in zip(tags, values) if t == "ints"): return "matrix"
    return None

def infer_types(tests):
    """-> {"args": [...], "ret": tag} or None when Java/C++ cannot represent this question."""
    try:
        n = len(tests[0]["input"])
        if any(len(t["input"]) != n for t in tests): return None
        args = []
        for i in range(n):
            vals = [t["input"][i] for t in tests]
            a = _merge([_tag(v) for v in vals], vals)
            if a is None: return None
            args.append(a)
        vals = [t["expected"] for t in tests]
        r = _merge([_tag(v) for v in vals], vals)
        return None if r is None else {"args": args, "ret": r}
    except Exception:
        return None

def param_names(py_starter):
    try:
        for n in ast.parse(py_starter).body:
            if isinstance(n, ast.FunctionDef) and n.name == "solution":
                return [a.arg for a in n.args.args]
    except SyntaxError:
        pass
    return None

JAVA_T = {"int": "int", "bool": "boolean", "str": "String", "ints": "int[]", "matrix": "int[][]"}
CPP_T = {"int": "int", "bool": "bool", "str": "string", "ints": "vector<int>", "matrix": "vector<vector<int>>"}
JAVA_D = {"int": "0", "bool": "false", "str": '""', "ints": "new int[0]", "matrix": "new int[0][0]"}
CPP_D = {"int": "0", "bool": "false", "str": '""', "ints": "{}", "matrix": "{}"}

def starters(q):
    """Starter code for every language this question supports."""
    out = {"python": q["starter_code"]}
    names = param_names(q["starter_code"])
    if not names:
        return out
    names = [n + "_" if n in RESERVED else n for n in names]
    out["javascript"] = f"function solution({', '.join(names)}) {{\n    // Write your code here\n}}\n"
    t = infer_types(q["test_cases"])
    if t and len(t["args"]) == len(names):
        ps = lambda M: ", ".join(f"{M[a]} {n}" for a, n in zip(t["args"], names))
        out["java"] = (f"class Solution {{\n    public static {JAVA_T[t['ret']]} solution({ps(JAVA_T)}) {{\n"
                       f"        // Write your code here\n        return {JAVA_D[t['ret']]};\n    }}\n}}\n")
        out["cpp"] = (f"// Write your code here\n{CPP_T[t['ret']]} solution({ps(CPP_T)}) {{\n"
                      f"    return {CPP_D[t['ret']]};\n}}\n")
    return out

def encode_input(types, tests):
    """One line per argument: ints/matrix as numbers (rows split by ';'), strings raw. First line = number of tests."""
    def enc(tag, v):
        if tag == "bool": return "true" if v else "false"
        if tag in ("int", "str"): return str(v)
        if tag == "ints": return " ".join(map(str, v))
        return ";".join(" ".join(map(str, r)) for r in v)
    lines = [str(len(tests))]
    for t in tests:
        lines += [enc(tag, v) for tag, v in zip(types["args"], t["input"])]
    return "\n".join(lines) + "\n"

JAVA_HARNESS = r'''
class Main {
    static String rd(java.io.BufferedReader b) throws Exception { String s = b.readLine(); return s == null ? "" : s; }
    static int[] ints(String l) { l = l.trim(); if (l.isEmpty()) return new int[0]; String[] p = l.split("\\s+"); int[] a = new int[p.length]; for (int i = 0; i < a.length; i++) a[i] = Integer.parseInt(p[i]); return a; }
    static int[][] mat(String l) { if (l.trim().isEmpty()) return new int[0][]; String[] r = l.split(";"); int[][] m = new int[r.length][]; for (int i = 0; i < r.length; i++) m[i] = ints(r[i]); return m; }
    static String js(int v) { return String.valueOf(v); }
    static String js(boolean v) { return v ? "true" : "false"; }
    static String js(String s) { if (s == null) return "null"; return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""; }
    static String js(int[] a) { if (a == null) return "null"; StringBuilder b = new StringBuilder("["); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(","); b.append(a[i]); } return b.append("]").toString(); }
    static String js(int[][] m) { if (m == null) return "null"; StringBuilder b = new StringBuilder("["); for (int i = 0; i < m.length; i++) { if (i > 0) b.append(","); b.append(js(m[i])); } return b.append("]").toString(); }
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        int T = Integer.parseInt(rd(br).trim());
        java.io.PrintWriter out = new java.io.PrintWriter(new java.io.FileWriter("results.txt"));
        for (int t = 0; t < T; t++) {
            @READ@
            long s = System.nanoTime();
            try {
                String r = js(@CALL@);
                out.println("OK " + (System.nanoTime() - s) / 1000 + " " + r);
            } catch (Throwable e) {
                out.println("ERR " + (System.nanoTime() - s) / 1000 + " " + String.valueOf(e).replace('\n', ' '));
            }
            out.flush();
        }
        out.close();
    }
}
'''

CPP_HARNESS = r'''
static std::vector<int> _ints(const std::string& l) { std::istringstream is(l); std::vector<int> v; int x; while (is >> x) v.push_back(x); return v; }
static std::vector<std::vector<int>> _mat(const std::string& l) { std::vector<std::vector<int>> m; std::istringstream is(l); std::string r; while (std::getline(is, r, ';')) m.push_back(_ints(r)); return m; }
static std::string _js(int v) { return std::to_string(v); }
static std::string _js(bool v) { return v ? "true" : "false"; }
static std::string _js(const std::string& s) { std::string o = "\""; for (char c : s) { if (c == '"' || c == '\\') o += '\\'; o += c; } return o + "\""; }
static std::string _js(const std::vector<int>& a) { std::string o = "["; for (size_t i = 0; i < a.size(); i++) { if (i) o += ","; o += std::to_string(a[i]); } return o + "]"; }
static std::string _js(const std::vector<std::vector<int>>& m) { std::string o = "["; for (size_t i = 0; i < m.size(); i++) { if (i) o += ","; o += _js(m[i]); } return o + "]"; }
int main() {
    std::string l; std::getline(std::cin, l); int T = std::stoi(l);
    std::ofstream out("results.txt");
    for (int t = 0; t < T; t++) {
        @READ@
        auto s = std::chrono::steady_clock::now();
        auto us = [&]() { return (long long)std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - s).count(); };
        try { std::string r = _js(@CALL@); out << "OK " << us() << " " << r << std::endl; }
        catch (std::exception& e) { out << "ERR " << us() << " " << e.what() << std::endl; }
        catch (...) { out << "ERR " << us() << " unknown exception" << std::endl; }
    }
}
'''

def java_harness(types):
    P = {"int": "Integer.parseInt(l{i}.trim())", "bool": "Boolean.parseBoolean(l{i}.trim())", "str": "l{i}",
         "ints": "ints(l{i})", "matrix": "mat(l{i})"}
    read = " ".join(f"String l{i} = rd(br);" for i in range(len(types["args"])))
    call = "Solution.solution(" + ", ".join(P[a].format(i=i) for i, a in enumerate(types["args"])) + ")"
    return JAVA_HARNESS.replace("@READ@", read).replace("@CALL@", call)

def cpp_harness(types):
    P = {"int": "std::stoi(a{i})", "bool": "(a{i}.find(\"true\") != std::string::npos)", "str": "a{i}",
         "ints": "_ints(a{i})", "matrix": "_mat(a{i})"}
    read = " ".join(f"std::string a{i}; std::getline(std::cin, a{i});" for i in range(len(types["args"])))
    call = "solution(" + ", ".join(P[a].format(i=i) for i, a in enumerate(types["args"])) + ")"
    return CPP_HARNESS.replace("@READ@", read).replace("@CALL@", call)
