# 2025-1 capstone desgin project

### 프로젝트: MuseumGO



[2025-1_캡스톤디자인 중간발표_6조.pdf](https://github.com/user-attachments/files/21107953/2025-1_._6.pdf)


MuseumGO는 어린이들의 미술 교육에서 발생하는 이해력의 차이와 예술-기술 융합 교육의 부재라는 한계를 극복하고자 시작된 프로젝트입니다. 저희는 AR과 생성형 AI 기술을 활용하여 정적인 미술 작품에 생명을 불어넣고, 어린이들에게 몰입감 높은 학습 경험을 제공하는 것을 목표로 합니다. 저희는 사용자가 작품을 즐기는 과정을 4단계의 자동화된 파이프라인으로 설계했습니다. 먼저 사용자가 Unity 기반의 AR 앱에서 카메라로 작품을 비추면, GPT-4o Vision이 이미지를 분석하여 맞춤형 설명을 생성합니다. 이어서 생성된 설명을 바탕으로 ElevenLabs TTS가 자연스러운 음성을 만들고, SadTalker가 이 음성에 맞춰 그림 속 인물의 입모양과 표정을 움직이는 립싱크 영상을 제작하여 작품이 직접 말을 거는 듯한 경험을 제공합니다. 인물화가 아닐 경우, Live2D SDK로 작가 캐릭터 애니메이션을 생성하는 방안도 고려했습니다. 이러한 시스템은 Unity 클라이언트와 Flask 백엔드 서버를 중심으로 구성되며, GPU 서버에서 SadTalker와 ffmpeg 같은 무거운 AI 모델을 실행하고 MySQL로 사용자 정보와 생성 기록을 관리합니다. 이 설계를 바탕으로 저희는 어린이 관람객과 교육 기관을 주요 사용자로 하여, 기존에 없던 새로운 방식의 AI 융합 미술 교육 솔루션을 제시하고자 합니다.







[2025-1_캡스톤디자인 기말발표_6조.pdf](https://github.com/user-attachments/files/21107959/2025-1_._6.pdf)


MuseumGO는 "생성형 AI가 딱딱한 미술 교육의 해답이 될 수 있을까?"라는 질문에서 출발하여, AR 기술로 그림과 실시간 상호작용을 구현한 프로젝트입니다. 저희는 중간 발표 이후 제기된 기술적 한계를 극복하고 사용자 경험을 혁신하는 데 집중했습니다. 초기 모델은 순차적인 처리 구조로 인해 10초 이상의 응답 지연과 GPU 유휴 상태 같은 자원 낭비 문제를 안고 있었습니다. 이 '10초의 벽'을 넘기 위해 저희는 백엔드 시스템을 전면적으로 재설계했습니다. 먼저 기존 Flask 서버를 FastAPI로 전환하여 비동기 처리를 도입했고, 메인 프로세스와 AI 모델을 실행하는 워커 프로세스를 분리하여 SadTalker 같은 모델을 미리 메모리에 로드함으로써 초기화 시간을 제거했습니다. 사용자 경험을 혁신하기 위해 선제적 파이프라인을 도입하여, 최종 영상이 제작되는 동안 GPU 유휴 시간을 활용해 약 4.5초 분량의 짧은 '인사 영상'을 먼저 제공하고, 이어서 퀴즈를 제시하여 대기 시간을 교육적 경험으로 전환시켰습니다. 이러한 최적화를 통해 '인사 영상'은 약 4.5초, '최종 영상'은 약 7.5초 만에 제공하는 등 실시간에 가까운 응답 속도를 달성했습니다. 또한, 촬영 이미지 미저장, TTS 음성 편향 최소화 등 윤리적, 안전적 측면을 고려하여, 안정성과 경제성, 교육적 효과를 모두 갖춘 지속 가능한 AI 융합 교육 솔루션으로 완성했습니다.


![image](https://github.com/user-attachments/assets/b1c76304-dfac-4ddf-a764-52bd9d2131ec)


![image](https://github.com/user-attachments/assets/e5b06a98-2c2e-433b-b322-de176d51c815)


![image](https://github.com/user-attachments/assets/3565c4a5-6264-497f-a590-6a576db749c6)



