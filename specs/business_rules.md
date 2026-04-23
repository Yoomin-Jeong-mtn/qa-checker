# 비즈니스 규칙 메모

시스템이 자동 판단할 수 없는 다중 프로퍼티 관계 규칙.
QA 시 수동으로 확인해야 하는 항목들.

| 이벤트 | 관련 프로퍼티 | 규칙 |
|--------|-------------|------|
| 공통 | deal_name, deal_end_time | deal_name=타임딜이면 deal_end_time 포함 가능. 쇼킹딜이면 미포함. 딜 진행 중인데 deal_name 없으면 사람이 판단 필요 |
| 공통 | platform, path | ANDROID_APP/IOS_APP/iOS_APP일 때 path는 null 허용. MW/PC일 때 path 값 필수 (URL 경로). 자동 검증 불가, 수동 확인 필요 |
| wish_remove | catalog_no, prd_svc_grp_cd, prd_svc_grp_dtl_cd | catalog_no가 있으면 prd_svc_grp_cd는 enum(01/02/03), prd_svc_grp_dtl_cd는 숫자 패턴이어야 함. 자동 검증 불가, 수동 확인 필요 |
