#!/usr/bin/env bash
# JoF revision: run the remaining CPU-bound steps in order, after N2 (classical extras) finishes.
# Each step logs to logs/; the pipeline stops at the first failure.
set -e
cd "$(dirname "$0")/.."

echo "[$(date +%T)] waiting for N2_classical_extras (36 cells)"
until [ "$(ls results/classical_extra/*.npz 2>/dev/null | wc -l)" -ge 36 ]; do sleep 60; done

echo "[$(date +%T)] N4 extended simulation analysis";   python code/N4_revision_analysis.py > logs/n4_analysis.log 2>&1
echo "[$(date +%T)] R2 robust rerun, 200 reps, phase A"; python code/R2_run_robust.py --reps 200 --n-jobs 8 --phase A > logs/robust_r200_A.log 2>&1
echo "[$(date +%T)] R2 phase B (GPU) and C";            python code/R2_run_robust.py --reps 200 --phase BC > logs/robust_r200_BC.log 2>&1
echo "[$(date +%T)] R4 and R5 robust analyses";          python code/R4_analyse_robust.py > logs/r4.log 2>&1; python code/R5_robust_uncertainty.py > logs/r5.log 2>&1
echo "[$(date +%T)] N3 M4 official, classical";          python code/N3_m4_official.py --phase A --n-jobs 8 > logs/m4_official_A.log 2>&1
echo "[$(date +%T)] N3 scoring";                         python code/N3_m4_official.py --phase C > logs/m4_official_C.log 2>&1
echo "[$(date +%T)] pipeline done"
