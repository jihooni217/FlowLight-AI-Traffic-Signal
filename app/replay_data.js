// FlowLight 녹화 재생 데이터: 실제 Solar Pro 4 응답 기록 (record_replay.py 로 생성, 손으로 편집하지 않음)
// 서버 없이 index.html 을 열었을 때 AI 분석 버튼이 이 이벤트를 원래 시간 간격대로 재생한다.
window.FLOWLIGHT_REPLAY = {
 "recorded_at": "2026-09-17",
 "model": "solar-pro4",
 "note": "실데이터 프로파일 08시, 차로 수는 데이터대로(남북 3·동서 2), 혼잡 배율 ×3, 주기 30초, 시드 20260702, 워밍업 120초 상태에서 기록한 실제 응답입니다. 사람이 고치거나 다듬지 않았습니다.",
 "request": {
  "intersection_id": "simulation-current",
  "tick": 120,
  "signals": {
   "cycle_sec": 30
  },
  "queues": {
   "total_cars": 35,
   "stopped_cars": 30,
   "by_approach": {
    "N": {
     "queue": 8,
     "mean_wait_sec": 10.1,
     "arrivals_last_window": 15,
     "saturation": 1.57,
     "lanes": 3
    },
    "S": {
     "queue": 10,
     "mean_wait_sec": 16.7,
     "arrivals_last_window": 9,
     "saturation": 1,
     "lanes": 3
    },
    "E": {
     "queue": 6,
     "mean_wait_sec": 3.2,
     "arrivals_last_window": 16,
     "saturation": 2.86,
     "lanes": 2
    },
    "W": {
     "queue": 6,
     "mean_wait_sec": 3.5,
     "arrivals_last_window": 12,
     "saturation": 2.29,
     "lanes": 2
    }
   }
  },
  "pedestrians": {
   "waiting_or_crossing": 0,
   "vulnerable_count": 0
  },
  "context": {
   "source": "flowlight_index_html",
   "grid_size": 3,
   "demand_mode": "profile",
   "by_approach_scope": "intersection_approaches",
   "window_sec": 30
  },
  "metrics": {
   "congestion": 1,
   "throughput_per_min": 92
  },
  "demand": {
   "mode": "profile",
   "site_id": "DEMO-X",
   "hour": 8,
   "unit": "veh_per_hour",
   "volume_per_hour": {
    "N": 842,
    "S": 790,
    "E": 610,
    "W": 655
   },
   "lanes": {
    "N": 3,
    "S": 3,
    "E": 2,
    "W": 2
   },
   "arrival_rate_per_sec": {
    "N": 0.077963,
    "S": 0.073148,
    "E": 0.084722,
    "W": 0.090972
   },
   "demo_scale": 3,
   "lost_demand_last_60s": {
    "N": 13,
    "S": 6,
    "E": 5,
    "W": 6
   },
   "note": "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. 둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다. demo_scale 은 데모용 혼잡 배율로, 실제 생성률은 arrival_rate_per_sec × 차로 수 × demo_scale 이다."
  }
 },
 "events": [
  {
   "t": 0,
   "event": "message",
   "data": {
    "step": 1,
    "message": "시뮬레이션 데이터 수신 완료"
   }
  },
  {
   "t": 0,
   "event": "message",
   "data": {
    "step": 2,
    "message": "교통 상황 분석 시작"
   }
  },
  {
   "t": 7.72,
   "event": "message",
   "data": {
    "step": 3,
    "message": "신호 계획 생성 시작"
   }
  },
  {
   "t": 19.25,
   "event": "message",
   "data": {
    "step": "guardrail",
    "message": "최소 신호 시간 Guardrail 적용 완료",
    "durations": {
     "north_south_green_sec": 8,
     "east_west_green_sec": 22,
     "pedestrian_green_sec": 0
    },
    "before": {
     "north_south_green_sec": 8,
     "east_west_green_sec": 22,
     "pedestrian_green_sec": 0
    }
   }
  },
  {
   "t": 19.25,
   "event": "message",
   "data": {
    "step": 4,
    "message": "계획 평가 시작"
   }
  },
  {
   "t": 21.36,
   "event": "done",
   "data": {
    "input_state": {
     "intersection_id": "simulation-current",
     "tick": 120,
     "signals": {
      "cycle_sec": 30
     },
     "queues": {
      "total_cars": 35,
      "stopped_cars": 30,
      "by_approach": {
       "N": {
        "queue": 8,
        "mean_wait_sec": 10.1,
        "arrivals_last_window": 15,
        "saturation": 1.57,
        "lanes": 3
       },
       "S": {
        "queue": 10,
        "mean_wait_sec": 16.7,
        "arrivals_last_window": 9,
        "saturation": 1,
        "lanes": 3
       },
       "E": {
        "queue": 6,
        "mean_wait_sec": 3.2,
        "arrivals_last_window": 16,
        "saturation": 2.86,
        "lanes": 2
       },
       "W": {
        "queue": 6,
        "mean_wait_sec": 3.5,
        "arrivals_last_window": 12,
        "saturation": 2.29,
        "lanes": 2
       }
      }
     },
     "pedestrians": {
      "waiting_or_crossing": 0,
      "vulnerable_count": 0
     },
     "context": {
      "source": "flowlight_index_html",
      "grid_size": 3,
      "demand_mode": "profile",
      "by_approach_scope": "intersection_approaches",
      "window_sec": 30
     },
     "metrics": {
      "congestion": 1,
      "throughput_per_min": 92
     },
     "demand": {
      "mode": "profile",
      "site_id": "DEMO-X",
      "hour": 8,
      "unit": "veh_per_hour",
      "volume_per_hour": {
       "N": 842,
       "S": 790,
       "E": 610,
       "W": 655
      },
      "lanes": {
       "N": 3,
       "S": 3,
       "E": 2,
       "W": 2
      },
      "arrival_rate_per_sec": {
       "N": 0.077963,
       "S": 0.073148,
       "E": 0.084722,
       "W": 0.090972
      },
      "demo_scale": 3,
      "lost_demand_last_60s": {
       "N": 13,
       "S": 6,
       "E": 5,
       "W": 6
      },
      "note": "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. 둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다. demo_scale 은 데모용 혼잡 배율로, 실제 생성률은 arrival_rate_per_sec × 차로 수 × demo_scale 이다."
     }
    },
    "traffic_analysis": {
     "summary": "현재 총 차량 35대 중 정지 차량이 30대로 많고 혼잡도 1.0으로 매우 높다. 접근로별 포화도는 E(2.86), W(2.29), N(1.57), S(1.0) 순으로 높아 동서 방향(E, W)이 가장 혼잡하며, 특히 E 접근로는 대기 차량 6대, W 접근로는 6대가 정체되어 있다. 보행자는 대기·횡단 0명, 교통약자 0명으로 보행자 이슈는 없다.",
     "traffic_level": "높음",
     "main_congestion_direction": "동서",
     "pedestrian_issue": false,
     "vulnerable_user_detected": false,
     "risk_level": "보통"
    },
    "signal_plan": {
     "plan_id": "PLAN-001",
     "next_signals": {
      "north_south": "RED",
      "east_west": "GREEN",
      "pedestrian": "RED"
     },
     "durations": {
      "north_south_green_sec": 8,
      "east_west_green_sec": 22,
      "pedestrian_green_sec": 0
     },
     "priority": "VEHICLE",
     "explanation": "보행자가 0명이므로 pedestrian_green_sec는 0, priority는 VEHICLE로 설정한다. queues.by_approach 기준 포화도 합은 동서(E+W=5.15)가 남북(N+S=2.57)보다 약 2배 높아 동서 축에 차량 녹색을 더 배분한다. 동서 축의 mean_wait_sec는 3초대로 짧지만 saturation이 매우 높아 처리 용량 대비 도착량이 많으므로, cycle_sec 30초 내에서 동서 22초·남북 8초로 배분한다. 남북 축은 포화도가 낮지만 N의 mean_wait_sec가 10.1초, S가 16.7초로 cycle_sec의 2배(60초)를 넘지 않으므로 최소 녹색 8초를 보장한다. traffic_level이 높음이고 congestion 1.0, stopped_cars 30대로 정체가 심해 동서 녹색을 12초 이상으로 길게 주었다. 전체 합계 30초는 cycle_sec를 초과하지 않는다."
    },
    "evaluation": {
     "total_score": 82,
     "scores": {
      "vehicle": 22,
      "pedestrian": 15,
      "vulnerable_user": 15,
      "safety": 18,
      "efficiency": 12
     },
     "decision_recommendation": "자동 적용",
     "reason": "보행자 대기 0명, 교통약자 0명으로 보행자 신호 0초는 적절하며, 혼잡도 1.0, 정지 차량 30대, 포화도 동서 5.15로 차량 수요가 높아 동서 녹색 22초 배분은 혼잡 대응에 타당하다. 신호 합계 30초는 cycle_sec 30초 이내이며, 보행자 이슈 없고 자동 적용 조건(보행자 0, 교통수준 높음, 혼잡도 0.7 이상, 정지 차량 20대 이상, 보행자 녹색 0초, 합계 이내)을 모두 만족하므로 자동 적용으로 판단한다. 백엔드 검증 결과, 보행자가 없고 차량 혼잡이 높아 자동 적용으로 보정했습니다."
    },
    "final_decision": "자동 적용"
   }
  }
 ]
};
