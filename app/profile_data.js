// FlowLight 내장 교통 수요 프로파일 (scripts/build_profile_data.py 로 생성)
// 서버 없이 열었을 때 실데이터 프로파일 모드가 이 데이터를 쓴다.
// FLOWLIGHT_PROFILE = 기본 프로파일 (GET /api/traffic/profile 과 같음)
// FLOWLIGHT_PROFILE_LIST = GET /api/traffic/profiles, FLOWLIGHT_PROFILE_DATA[id] = GET /api/traffic/profile?profile=id
window.FLOWLIGHT_PROFILE = {
 "meta": {
  "site_id": "DEMO-X",
  "site_name": "FlowLight 데모 교차로 (합성 예제, 서울시 교통량 이력 정보 컬럼 구조)",
  "date": "20250514",
  "weekday": "Wed",
  "source": "합성 예제. 컬럼 구조는 서울특별시_교통량 이력 정보(공공데이터포털 15056899, 원천 TOPIS)를 따름. 값은 data/README.md 의 공식으로 생성",
  "license": "예제 데이터는 이 저장소 라이선스를 따름. 원본 데이터셋은 공공데이터포털 표기상 '이용허락범위 제한 없음'",
  "unit": "veh_per_hour",
  "lanes": {
   "N": 3,
   "S": 3,
   "E": 2,
   "W": 2
  },
  "approach_names": {},
  "profile_file": "sample_seoul_traffic_history.meta.json",
  "approach_naming": "N = 북측에서 진입해 남쪽으로 향하는 차량 (S/E/W 도 같은 규칙)",
  "note": "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. 둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다."
 },
 "available_hours": [
  0,
  1,
  2,
  3,
  4,
  5,
  6,
  7,
  8,
  9,
  10,
  11,
  12,
  13,
  14,
  15,
  16,
  17,
  18,
  19,
  20,
  21,
  22,
  23
 ],
 "hours": [
  {
   "hour": 0,
   "volume": {
    "N": 84,
    "S": 79,
    "E": 61,
    "W": 66
   },
   "arrival_rate_per_sec": {
    "N": 0.007778,
    "S": 0.007315,
    "E": 0.008472,
    "W": 0.009167
   }
  },
  {
   "hour": 1,
   "volume": {
    "N": 51,
    "S": 47,
    "E": 37,
    "W": 39
   },
   "arrival_rate_per_sec": {
    "N": 0.004722,
    "S": 0.004352,
    "E": 0.005139,
    "W": 0.005417
   }
  },
  {
   "hour": 2,
   "volume": {
    "N": 34,
    "S": 32,
    "E": 24,
    "W": 26
   },
   "arrival_rate_per_sec": {
    "N": 0.003148,
    "S": 0.002963,
    "E": 0.003333,
    "W": 0.003611
   }
  },
  {
   "hour": 3,
   "volume": {
    "N": 25,
    "S": 24,
    "E": 18,
    "W": 20
   },
   "arrival_rate_per_sec": {
    "N": 0.002315,
    "S": 0.002222,
    "E": 0.0025,
    "W": 0.002778
   }
  },
  {
   "hour": 4,
   "volume": {
    "N": 34,
    "S": 32,
    "E": 24,
    "W": 26
   },
   "arrival_rate_per_sec": {
    "N": 0.003148,
    "S": 0.002963,
    "E": 0.003333,
    "W": 0.003611
   }
  },
  {
   "hour": 5,
   "volume": {
    "N": 84,
    "S": 79,
    "E": 61,
    "W": 66
   },
   "arrival_rate_per_sec": {
    "N": 0.007778,
    "S": 0.007315,
    "E": 0.008472,
    "W": 0.009167
   }
  },
  {
   "hour": 6,
   "volume": {
    "N": 253,
    "S": 237,
    "E": 183,
    "W": 196
   },
   "arrival_rate_per_sec": {
    "N": 0.023426,
    "S": 0.021944,
    "E": 0.025417,
    "W": 0.027222
   }
  },
  {
   "hour": 7,
   "volume": {
    "N": 632,
    "S": 592,
    "E": 458,
    "W": 491
   },
   "arrival_rate_per_sec": {
    "N": 0.058519,
    "S": 0.054815,
    "E": 0.063611,
    "W": 0.068194
   }
  },
  {
   "hour": 8,
   "volume": {
    "N": 842,
    "S": 790,
    "E": 610,
    "W": 655
   },
   "arrival_rate_per_sec": {
    "N": 0.077963,
    "S": 0.073148,
    "E": 0.084722,
    "W": 0.090972
   }
  },
  {
   "hour": 9,
   "volume": {
    "N": 674,
    "S": 632,
    "E": 488,
    "W": 524
   },
   "arrival_rate_per_sec": {
    "N": 0.062407,
    "S": 0.058519,
    "E": 0.067778,
    "W": 0.072778
   }
  },
  {
   "hour": 10,
   "volume": {
    "N": 547,
    "S": 514,
    "E": 396,
    "W": 426
   },
   "arrival_rate_per_sec": {
    "N": 0.050648,
    "S": 0.047593,
    "E": 0.055,
    "W": 0.059167
   }
  },
  {
   "hour": 11,
   "volume": {
    "N": 547,
    "S": 514,
    "E": 396,
    "W": 426
   },
   "arrival_rate_per_sec": {
    "N": 0.050648,
    "S": 0.047593,
    "E": 0.055,
    "W": 0.059167
   }
  },
  {
   "hour": 12,
   "volume": {
    "N": 589,
    "S": 553,
    "E": 427,
    "W": 458
   },
   "arrival_rate_per_sec": {
    "N": 0.054537,
    "S": 0.051204,
    "E": 0.059306,
    "W": 0.063611
   }
  },
  {
   "hour": 13,
   "volume": {
    "N": 573,
    "S": 537,
    "E": 415,
    "W": 445
   },
   "arrival_rate_per_sec": {
    "N": 0.053056,
    "S": 0.049722,
    "E": 0.057639,
    "W": 0.061806
   }
  },
  {
   "hour": 14,
   "volume": {
    "N": 556,
    "S": 521,
    "E": 403,
    "W": 432
   },
   "arrival_rate_per_sec": {
    "N": 0.051481,
    "S": 0.048241,
    "E": 0.055972,
    "W": 0.06
   }
  },
  {
   "hour": 15,
   "volume": {
    "N": 589,
    "S": 553,
    "E": 427,
    "W": 458
   },
   "arrival_rate_per_sec": {
    "N": 0.054537,
    "S": 0.051204,
    "E": 0.059306,
    "W": 0.063611
   }
  },
  {
   "hour": 16,
   "volume": {
    "N": 674,
    "S": 632,
    "E": 488,
    "W": 524
   },
   "arrival_rate_per_sec": {
    "N": 0.062407,
    "S": 0.058519,
    "E": 0.067778,
    "W": 0.072778
   }
  },
  {
   "hour": 17,
   "volume": {
    "N": 800,
    "S": 750,
    "E": 580,
    "W": 622
   },
   "arrival_rate_per_sec": {
    "N": 0.074074,
    "S": 0.069444,
    "E": 0.080556,
    "W": 0.086389
   }
  },
  {
   "hour": 18,
   "volume": {
    "N": 758,
    "S": 711,
    "E": 549,
    "W": 590
   },
   "arrival_rate_per_sec": {
    "N": 0.070185,
    "S": 0.065833,
    "E": 0.07625,
    "W": 0.081944
   }
  },
  {
   "hour": 19,
   "volume": {
    "N": 589,
    "S": 553,
    "E": 427,
    "W": 458
   },
   "arrival_rate_per_sec": {
    "N": 0.054537,
    "S": 0.051204,
    "E": 0.059306,
    "W": 0.063611
   }
  },
  {
   "hour": 20,
   "volume": {
    "N": 463,
    "S": 435,
    "E": 336,
    "W": 360
   },
   "arrival_rate_per_sec": {
    "N": 0.04287,
    "S": 0.040278,
    "E": 0.046667,
    "W": 0.05
   }
  },
  {
   "hour": 21,
   "volume": {
    "N": 379,
    "S": 356,
    "E": 274,
    "W": 295
   },
   "arrival_rate_per_sec": {
    "N": 0.035093,
    "S": 0.032963,
    "E": 0.038056,
    "W": 0.040972
   }
  },
  {
   "hour": 22,
   "volume": {
    "N": 253,
    "S": 237,
    "E": 183,
    "W": 196
   },
   "arrival_rate_per_sec": {
    "N": 0.023426,
    "S": 0.021944,
    "E": 0.025417,
    "W": 0.027222
   }
  },
  {
   "hour": 23,
   "volume": {
    "N": 152,
    "S": 142,
    "E": 110,
    "W": 118
   },
   "arrival_rate_per_sec": {
    "N": 0.014074,
    "S": 0.013148,
    "E": 0.015278,
    "W": 0.016389
   }
  }
 ]
};
window.FLOWLIGHT_PROFILE_LIST = {
 "default": "sample_seoul_traffic_history",
 "profiles": [
  {
   "id": "sample_seoul_traffic_history",
   "file": "sample_seoul_traffic_history.meta.json",
   "site_name": "FlowLight 데모 교차로 (합성 예제, 서울시 교통량 이력 정보 컬럼 구조)",
   "date": "20250514",
   "default": true
  },
  {
   "id": "seoul_sungnyemun_20260916",
   "file": "seoul_sungnyemun_20260916.meta.json",
   "site_name": "서울 숭례문 일대 실측 (세종대로·퇴계로·서소문로, 2026-09-16 수)",
   "date": "20260916",
   "default": false
  }
 ]
};
window.FLOWLIGHT_PROFILE_DATA = {
 "sample_seoul_traffic_history": {
  "meta": {
   "site_id": "DEMO-X",
   "site_name": "FlowLight 데모 교차로 (합성 예제, 서울시 교통량 이력 정보 컬럼 구조)",
   "date": "20250514",
   "weekday": "Wed",
   "source": "합성 예제. 컬럼 구조는 서울특별시_교통량 이력 정보(공공데이터포털 15056899, 원천 TOPIS)를 따름. 값은 data/README.md 의 공식으로 생성",
   "license": "예제 데이터는 이 저장소 라이선스를 따름. 원본 데이터셋은 공공데이터포털 표기상 '이용허락범위 제한 없음'",
   "unit": "veh_per_hour",
   "lanes": {
    "N": 3,
    "S": 3,
    "E": 2,
    "W": 2
   },
   "approach_names": {},
   "profile_file": "sample_seoul_traffic_history.meta.json",
   "approach_naming": "N = 북측에서 진입해 남쪽으로 향하는 차량 (S/E/W 도 같은 규칙)",
   "note": "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. 둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다."
  },
  "available_hours": [
   0,
   1,
   2,
   3,
   4,
   5,
   6,
   7,
   8,
   9,
   10,
   11,
   12,
   13,
   14,
   15,
   16,
   17,
   18,
   19,
   20,
   21,
   22,
   23
  ],
  "hours": [
   {
    "hour": 0,
    "volume": {
     "N": 84,
     "S": 79,
     "E": 61,
     "W": 66
    },
    "arrival_rate_per_sec": {
     "N": 0.007778,
     "S": 0.007315,
     "E": 0.008472,
     "W": 0.009167
    }
   },
   {
    "hour": 1,
    "volume": {
     "N": 51,
     "S": 47,
     "E": 37,
     "W": 39
    },
    "arrival_rate_per_sec": {
     "N": 0.004722,
     "S": 0.004352,
     "E": 0.005139,
     "W": 0.005417
    }
   },
   {
    "hour": 2,
    "volume": {
     "N": 34,
     "S": 32,
     "E": 24,
     "W": 26
    },
    "arrival_rate_per_sec": {
     "N": 0.003148,
     "S": 0.002963,
     "E": 0.003333,
     "W": 0.003611
    }
   },
   {
    "hour": 3,
    "volume": {
     "N": 25,
     "S": 24,
     "E": 18,
     "W": 20
    },
    "arrival_rate_per_sec": {
     "N": 0.002315,
     "S": 0.002222,
     "E": 0.0025,
     "W": 0.002778
    }
   },
   {
    "hour": 4,
    "volume": {
     "N": 34,
     "S": 32,
     "E": 24,
     "W": 26
    },
    "arrival_rate_per_sec": {
     "N": 0.003148,
     "S": 0.002963,
     "E": 0.003333,
     "W": 0.003611
    }
   },
   {
    "hour": 5,
    "volume": {
     "N": 84,
     "S": 79,
     "E": 61,
     "W": 66
    },
    "arrival_rate_per_sec": {
     "N": 0.007778,
     "S": 0.007315,
     "E": 0.008472,
     "W": 0.009167
    }
   },
   {
    "hour": 6,
    "volume": {
     "N": 253,
     "S": 237,
     "E": 183,
     "W": 196
    },
    "arrival_rate_per_sec": {
     "N": 0.023426,
     "S": 0.021944,
     "E": 0.025417,
     "W": 0.027222
    }
   },
   {
    "hour": 7,
    "volume": {
     "N": 632,
     "S": 592,
     "E": 458,
     "W": 491
    },
    "arrival_rate_per_sec": {
     "N": 0.058519,
     "S": 0.054815,
     "E": 0.063611,
     "W": 0.068194
    }
   },
   {
    "hour": 8,
    "volume": {
     "N": 842,
     "S": 790,
     "E": 610,
     "W": 655
    },
    "arrival_rate_per_sec": {
     "N": 0.077963,
     "S": 0.073148,
     "E": 0.084722,
     "W": 0.090972
    }
   },
   {
    "hour": 9,
    "volume": {
     "N": 674,
     "S": 632,
     "E": 488,
     "W": 524
    },
    "arrival_rate_per_sec": {
     "N": 0.062407,
     "S": 0.058519,
     "E": 0.067778,
     "W": 0.072778
    }
   },
   {
    "hour": 10,
    "volume": {
     "N": 547,
     "S": 514,
     "E": 396,
     "W": 426
    },
    "arrival_rate_per_sec": {
     "N": 0.050648,
     "S": 0.047593,
     "E": 0.055,
     "W": 0.059167
    }
   },
   {
    "hour": 11,
    "volume": {
     "N": 547,
     "S": 514,
     "E": 396,
     "W": 426
    },
    "arrival_rate_per_sec": {
     "N": 0.050648,
     "S": 0.047593,
     "E": 0.055,
     "W": 0.059167
    }
   },
   {
    "hour": 12,
    "volume": {
     "N": 589,
     "S": 553,
     "E": 427,
     "W": 458
    },
    "arrival_rate_per_sec": {
     "N": 0.054537,
     "S": 0.051204,
     "E": 0.059306,
     "W": 0.063611
    }
   },
   {
    "hour": 13,
    "volume": {
     "N": 573,
     "S": 537,
     "E": 415,
     "W": 445
    },
    "arrival_rate_per_sec": {
     "N": 0.053056,
     "S": 0.049722,
     "E": 0.057639,
     "W": 0.061806
    }
   },
   {
    "hour": 14,
    "volume": {
     "N": 556,
     "S": 521,
     "E": 403,
     "W": 432
    },
    "arrival_rate_per_sec": {
     "N": 0.051481,
     "S": 0.048241,
     "E": 0.055972,
     "W": 0.06
    }
   },
   {
    "hour": 15,
    "volume": {
     "N": 589,
     "S": 553,
     "E": 427,
     "W": 458
    },
    "arrival_rate_per_sec": {
     "N": 0.054537,
     "S": 0.051204,
     "E": 0.059306,
     "W": 0.063611
    }
   },
   {
    "hour": 16,
    "volume": {
     "N": 674,
     "S": 632,
     "E": 488,
     "W": 524
    },
    "arrival_rate_per_sec": {
     "N": 0.062407,
     "S": 0.058519,
     "E": 0.067778,
     "W": 0.072778
    }
   },
   {
    "hour": 17,
    "volume": {
     "N": 800,
     "S": 750,
     "E": 580,
     "W": 622
    },
    "arrival_rate_per_sec": {
     "N": 0.074074,
     "S": 0.069444,
     "E": 0.080556,
     "W": 0.086389
    }
   },
   {
    "hour": 18,
    "volume": {
     "N": 758,
     "S": 711,
     "E": 549,
     "W": 590
    },
    "arrival_rate_per_sec": {
     "N": 0.070185,
     "S": 0.065833,
     "E": 0.07625,
     "W": 0.081944
    }
   },
   {
    "hour": 19,
    "volume": {
     "N": 589,
     "S": 553,
     "E": 427,
     "W": 458
    },
    "arrival_rate_per_sec": {
     "N": 0.054537,
     "S": 0.051204,
     "E": 0.059306,
     "W": 0.063611
    }
   },
   {
    "hour": 20,
    "volume": {
     "N": 463,
     "S": 435,
     "E": 336,
     "W": 360
    },
    "arrival_rate_per_sec": {
     "N": 0.04287,
     "S": 0.040278,
     "E": 0.046667,
     "W": 0.05
    }
   },
   {
    "hour": 21,
    "volume": {
     "N": 379,
     "S": 356,
     "E": 274,
     "W": 295
    },
    "arrival_rate_per_sec": {
     "N": 0.035093,
     "S": 0.032963,
     "E": 0.038056,
     "W": 0.040972
    }
   },
   {
    "hour": 22,
    "volume": {
     "N": 253,
     "S": 237,
     "E": 183,
     "W": 196
    },
    "arrival_rate_per_sec": {
     "N": 0.023426,
     "S": 0.021944,
     "E": 0.025417,
     "W": 0.027222
    }
   },
   {
    "hour": 23,
    "volume": {
     "N": 152,
     "S": 142,
     "E": 110,
     "W": 118
    },
    "arrival_rate_per_sec": {
     "N": 0.014074,
     "S": 0.013148,
     "E": 0.015278,
     "W": 0.016389
    }
   }
  ]
 },
 "seoul_sungnyemun_20260916": {
  "meta": {
   "site_id": "SUNGNYEMUN",
   "site_name": "서울 숭례문 일대 실측 (세종대로·퇴계로·서소문로, 2026-09-16 수)",
   "date": "20260916",
   "weekday": "Wed",
   "source": "서울특별시_교통량 이력 정보 (공공데이터포털 15056899 → 서울 열린데이터광장 VolInfo, 원천 TOPIS). 20260916 하루치를 scripts/fetch_seoul_traffic.py 로 받음. io_type 1→유입, 2→유출로 표기",
   "license": "공공데이터포털 표기상 이용허락범위 제한 없음. 출처: 서울특별시(TOPIS)",
   "unit": "veh_per_hour",
   "lanes": {
    "N": 5,
    "S": 4,
    "E": 2,
    "W": 3
   },
   "approach_names": {
    "N": "세종대로(시청역2)",
    "S": "세종대로(서울역)",
    "E": "퇴계로(회현역)",
    "W": "서소문로(시청역)"
   },
   "profile_file": "seoul_sungnyemun_20260916.meta.json",
   "approach_naming": "N = 북측에서 진입해 남쪽으로 향하는 차량 (S/E/W 도 같은 규칙)",
   "note": "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. 둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다."
  },
  "available_hours": [
   0,
   1,
   2,
   3,
   4,
   5,
   6,
   7,
   8,
   9,
   10,
   11,
   12,
   13,
   14,
   15,
   16,
   17,
   18,
   19,
   20,
   21,
   22,
   23
  ],
  "hours": [
   {
    "hour": 0,
    "volume": {
     "N": 443,
     "S": 501,
     "E": 491,
     "W": 339
    },
    "arrival_rate_per_sec": {
     "N": 0.024611,
     "S": 0.034792,
     "E": 0.068194,
     "W": 0.031389
    }
   },
   {
    "hour": 1,
    "volume": {
     "N": 243,
     "S": 426,
     "E": 367,
     "W": 325
    },
    "arrival_rate_per_sec": {
     "N": 0.0135,
     "S": 0.029583,
     "E": 0.050972,
     "W": 0.030093
    }
   },
   {
    "hour": 2,
    "volume": {
     "N": 157,
     "S": 304,
     "E": 291,
     "W": 227
    },
    "arrival_rate_per_sec": {
     "N": 0.008722,
     "S": 0.021111,
     "E": 0.040417,
     "W": 0.021019
    }
   },
   {
    "hour": 3,
    "volume": {
     "N": 154,
     "S": 192,
     "E": 222,
     "W": 209
    },
    "arrival_rate_per_sec": {
     "N": 0.008556,
     "S": 0.013333,
     "E": 0.030833,
     "W": 0.019352
    }
   },
   {
    "hour": 4,
    "volume": {
     "N": 280,
     "S": 301,
     "E": 314,
     "W": 336
    },
    "arrival_rate_per_sec": {
     "N": 0.015556,
     "S": 0.020903,
     "E": 0.043611,
     "W": 0.031111
    }
   },
   {
    "hour": 5,
    "volume": {
     "N": 579,
     "S": 622,
     "E": 690,
     "W": 478
    },
    "arrival_rate_per_sec": {
     "N": 0.032167,
     "S": 0.043194,
     "E": 0.095833,
     "W": 0.044259
    }
   },
   {
    "hour": 6,
    "volume": {
     "N": 1264,
     "S": 1177,
     "E": 1190,
     "W": 746
    },
    "arrival_rate_per_sec": {
     "N": 0.070222,
     "S": 0.081736,
     "E": 0.165278,
     "W": 0.069074
    }
   },
   {
    "hour": 7,
    "volume": {
     "N": 1889,
     "S": 1952,
     "E": 1249,
     "W": 999
    },
    "arrival_rate_per_sec": {
     "N": 0.104944,
     "S": 0.135556,
     "E": 0.173472,
     "W": 0.0925
    }
   },
   {
    "hour": 8,
    "volume": {
     "N": 2113,
     "S": 2049,
     "E": 1175,
     "W": 1101
    },
    "arrival_rate_per_sec": {
     "N": 0.117389,
     "S": 0.142292,
     "E": 0.163194,
     "W": 0.101944
    }
   },
   {
    "hour": 9,
    "volume": {
     "N": 1813,
     "S": 1949,
     "E": 1082,
     "W": 981
    },
    "arrival_rate_per_sec": {
     "N": 0.100722,
     "S": 0.135347,
     "E": 0.150278,
     "W": 0.090833
    }
   },
   {
    "hour": 10,
    "volume": {
     "N": 1766,
     "S": 1886,
     "E": 1126,
     "W": 902
    },
    "arrival_rate_per_sec": {
     "N": 0.098111,
     "S": 0.130972,
     "E": 0.156389,
     "W": 0.083519
    }
   },
   {
    "hour": 11,
    "volume": {
     "N": 1598,
     "S": 1942,
     "E": 1217,
     "W": 789
    },
    "arrival_rate_per_sec": {
     "N": 0.088778,
     "S": 0.134861,
     "E": 0.169028,
     "W": 0.073056
    }
   },
   {
    "hour": 12,
    "volume": {
     "N": 1700,
     "S": 1830,
     "E": 1085,
     "W": 793
    },
    "arrival_rate_per_sec": {
     "N": 0.094444,
     "S": 0.127083,
     "E": 0.150694,
     "W": 0.073426
    }
   },
   {
    "hour": 13,
    "volume": {
     "N": 1536,
     "S": 1406,
     "E": 1031,
     "W": 709
    },
    "arrival_rate_per_sec": {
     "N": 0.085333,
     "S": 0.097639,
     "E": 0.143194,
     "W": 0.065648
    }
   },
   {
    "hour": 14,
    "volume": {
     "N": 1681,
     "S": 1193,
     "E": 1057,
     "W": 556
    },
    "arrival_rate_per_sec": {
     "N": 0.093389,
     "S": 0.082847,
     "E": 0.146806,
     "W": 0.051481
    }
   },
   {
    "hour": 15,
    "volume": {
     "N": 1596,
     "S": 1296,
     "E": 1108,
     "W": 479
    },
    "arrival_rate_per_sec": {
     "N": 0.088667,
     "S": 0.09,
     "E": 0.153889,
     "W": 0.044352
    }
   },
   {
    "hour": 16,
    "volume": {
     "N": 1211,
     "S": 1019,
     "E": 1041,
     "W": 358
    },
    "arrival_rate_per_sec": {
     "N": 0.067278,
     "S": 0.070764,
     "E": 0.144583,
     "W": 0.033148
    }
   },
   {
    "hour": 17,
    "volume": {
     "N": 1280,
     "S": 1327,
     "E": 1091,
     "W": 513
    },
    "arrival_rate_per_sec": {
     "N": 0.071111,
     "S": 0.092153,
     "E": 0.151528,
     "W": 0.0475
    }
   },
   {
    "hour": 18,
    "volume": {
     "N": 1779,
     "S": 997,
     "E": 893,
     "W": 777
    },
    "arrival_rate_per_sec": {
     "N": 0.098833,
     "S": 0.069236,
     "E": 0.124028,
     "W": 0.071944
    }
   },
   {
    "hour": 19,
    "volume": {
     "N": 1235,
     "S": 1228,
     "E": 936,
     "W": 777
    },
    "arrival_rate_per_sec": {
     "N": 0.068611,
     "S": 0.085278,
     "E": 0.13,
     "W": 0.071944
    }
   },
   {
    "hour": 20,
    "volume": {
     "N": 1225,
     "S": 1115,
     "E": 931,
     "W": 673
    },
    "arrival_rate_per_sec": {
     "N": 0.068056,
     "S": 0.077431,
     "E": 0.129306,
     "W": 0.062315
    }
   },
   {
    "hour": 21,
    "volume": {
     "N": 1239,
     "S": 996,
     "E": 808,
     "W": 567
    },
    "arrival_rate_per_sec": {
     "N": 0.068833,
     "S": 0.069167,
     "E": 0.112222,
     "W": 0.0525
    }
   },
   {
    "hour": 22,
    "volume": {
     "N": 1069,
     "S": 959,
     "E": 748,
     "W": 549
    },
    "arrival_rate_per_sec": {
     "N": 0.059389,
     "S": 0.066597,
     "E": 0.103889,
     "W": 0.050833
    }
   },
   {
    "hour": 23,
    "volume": {
     "N": 785,
     "S": 831,
     "E": 692,
     "W": 428
    },
    "arrival_rate_per_sec": {
     "N": 0.043611,
     "S": 0.057708,
     "E": 0.096111,
     "W": 0.03963
    }
   }
  ]
 }
};
