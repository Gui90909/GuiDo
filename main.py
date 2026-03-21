from fastapi import FastAPI
from pydantic import BaseModel
import base64
import datetime

app = FastAPI()


class GenerateRequest(BaseModel):
    prompt: str
    language: str  # "python" | "cpp" | "matlab"
    projectName: str
    mode: str      # "conservador" | "equilibrat" | "agressiu"


def make_branch_name(project_name: str) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe = project_name.replace(" ", "_").lower()
    return f"gen/{safe}-{ts}"


# ------------------------------
# Generadors de fitxers per llenguatge
# ------------------------------

def generate_python(prompt: str, project: str, mode: str):
    src = f'''"""
{project} — generat des de prompt. Mode: {mode}
Codi compacte i comentat.
"""
from __future__ import annotations

def main(data: list[float]) -> dict[str, float]:
    """Calcula n, min, max, avg."""
    if not data:
        return {{"n": 0, "min": 0.0, "max": 0.0, "avg": 0.0}}
    n = len(data)
    mn = min(data)
    mx = max(data)
    avg = sum(data)/n
    return {{"n": n, "min": mn, "max": mx, "avg": avg}}
'''
    test = '''from src.module import main

def test_basic():
    r = main([1, 2, 3])
    assert r["n"] == 3 and r["min"] == 1 and r["max"] == 3 and abs(r["avg"] - 2.0) < 1e-12
'''
    return [
        {"path": "src/module.py", "content": src},
        {"path": "tests/test_module.py", "content": test},
        {"path": "README.md", "content": f"# {project}\n\nPrompt: {prompt}\nMode: {mode}\n"}
    ]


def generate_cpp(prompt: str, project: str, mode: str):
    hpp = f'''// {project} — Mode: {mode}
#pragma once
#include <vector>

struct Stats {{
    int n; double min, max, avg;
}};

Stats compute(const std::vector<double>& data);
'''
    cpp = '''#include "module.hpp"
#include <algorithm>
#include <numeric>

Stats compute(const std::vector<double>& v){
    if(v.empty()) return {0, 0.0, 0.0, 0.0};
    auto mm = std::minmax_element(v.begin(), v.end());
    double sum = std::accumulate(v.begin(), v.end(), 0.0);
    return {(int)v.size(), *mm.first, *mm.second, sum / v.size()};
}
'''
    test = '''#include "module.hpp"
#include <cassert>

int main(){
    auto r = compute({1.0, 2.0, 3.0});
    assert(r.n == 3 && r.min == 1.0 && r.max == 3.0 && (r.avg - 2.0) < 1e-12);
    return 0;
}
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


def generate_matlab(prompt: str, project: str, mode: str):
    """
    Genera un mòdul MATLAB minimalista. Crea una funció 'stats' a src/module.m
    que rep un vector i retorna una estructura amb n, min, max, avg.
    Inclou un test bàsic a tests/test_module.m amb asserts.
    """
    module_m = f'''% {project} — generat des de prompt
% Mode: {mode}
% Funció compacta i comentada que calcula n, min, max i avg d'un vector.

function r = module(data)
%MODULE Calcula estadístics bàsics d'un vector numèric.
%   r = MODULE(data) retorna una struct amb camps:
%   - n: nombre d'elements
%   - min: mínim
%   - max: màxim
%   - avg: mitjana

    if isempty(data)
        r = struct('n', 0, 'min', 0.0, 'max', 0.0, 'avg', 0.0);
        return;
    end

    n = numel(data);
    mn = min(data);
    mx = max(data);
    avg = mean(data);
    r = struct('n', n, 'min', mn, 'max', mx, 'avg', avg);
end
'''
    test_m = '''% Test bàsic per module.m
% Executa'l a MATLAB/Octave amb:  tests/test_module.m

addpath('src');
r = module([1, 2, 3]);

assert(r.n == 3, 'n incorrecte');
assert(abs(r.min - 1.0) < 1e-12, 'min incorrecte');
assert(abs(r.max - 3.0) < 1e-12, 'max incorrecte');
assert(abs(r.avg - 2.0) < 1e-12, 'avg incorrecte');

disp('tests/test_module.m: OK');
'''
    readme = f'''# {project} (MATLAB)

Prompt: {prompt}

Mode: {mode}

## Estructura
- `src/module.m` — funció **module(data)** que retorna una `struct` amb `n`, `min`, `max`, `avg`.
- `tests/test_module.m` — test bàsic amb `assert`.

## Ús ràpid (MATLAB o GNU Octave)
```matlab
addpath('src');
r = module([10 20 30]);
disp(r)
run('tests/test_module.m')
