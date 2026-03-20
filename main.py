from fastapi import FastAPI
from pydantic import BaseModel
import base64
import datetime

app = FastAPI()

class GenerateRequest(BaseModel):
    prompt: str
    language: str
    projectName: str
    mode: str

def make_branch_name(project_name: str) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe = project_name.replace(" ", "_").lower()
    return f"gen/{safe}-{ts}"

def generate_python(prompt, project, mode):
    src = f'''"""
{project} — generat des de prompt. Mode: {mode}
Codi compacte i comentat.
"""
from __future__ import annotations

def main(data: list[float]) -> dict[str, float]:
    """Calcula n, min, max, avg."""
    if not data: return {{ "n":0, "min":0.0, "max":0.0, "avg":0.0 }}
    n=len(data); mn=min(data); mx=max(data); avg=sum(data)/n
    return {{ "n": n, "min": mn, "max": mx, "avg": avg }}
'''
    test = '''from src.module import main
def test_basic():
    r = main([1,2,3])
    assert r["n"]==3 and r["min"]==1 and r["max"]==3 and abs(r["avg"]-2.0)<1e-12
'''
    return [
        {"path": "src/module.py", "content": src},
        {"path": "tests/test_module.py", "content": test},
        {"path": "README.md", "content": f"# {project}\n\nPrompt: {prompt}\nMode: {mode}\n"}
    ]

def generate_cpp(prompt, project, mode):
    hpp = f'''// {project} — Mode: {mode}
#pragma once
#include <vector>
struct Stats {{ int n; double min, max, avg; }};
Stats compute(const std::vector<double>& data);
'''
    cpp = '''#include "module.hpp"
#include <algorithm>
#include <numeric>
Stats compute(const std::vector<double>& v){
    if(v.empty()) return {0,0.0,0.0,0.0};
    auto mm = std::minmax_element(v.begin(),v.end());
    double sum = std::accumulate(v.begin(),v.end(),0.0);
    return {(int)v.size(), *mm.first, *mm.second, sum/v.size()};
}
'''
    test = '''#include "module.hpp"
#include <cassert>
int main(){ auto r = compute({1.0,2.0,3.0});
  assert(r.n==3 && r.min==1.0 && r.max==3.0 && (r.avg-2.0)<1e-12); return 0; }
'''
    cmake = '''cmake_minimum_required(VERSION 3.14)
project(genproj CXX)
set(CMAKE_CXX_STANDARD 17)
add_library(core src/module.cpp)
target_include_directories(core PUBLIC src)
add_executable(test_app tests/test.cpp)
target_link_libraries(test_app PRIVATE core)
'''
    return [
        {"path": "src/module.hpp", "content": hpp},
        {"path": "src/module.cpp", "content": cpp},
        {"path": "tests/test.cpp", "content": test},
        {"path": "CMakeLists.txt", "content": cmake},
        {"path": "README.md", "content": f"# {project}\n\nPrompt: {prompt}\nMode: {mode}\n"}
    ]

@app.post("/generate")
def generate(req: GenerateRequest):
    branch = make_branch_name(req.projectName)

    if req.language.lower() == "cpp":
        files = generate_cpp(req.prompt, req.projectName, req.mode)
    else:
        files = generate_python(req.prompt, req.projectName, req.mode)

    files_encoded = [
        {"path": f["path"], "contentBase64": base64.b64encode(f["content"].encode()).decode()}
        for f in files
    ]

    return {
        "branch": branch,
        "files": files_encoded,
        "summary": f"Projecte '{req.projectName}' ({req.language}) generat en mode {req.mode}."
    }
