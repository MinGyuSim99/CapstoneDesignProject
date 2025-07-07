using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using TMPro;
using System.IO;

public class ImageSender : MonoBehaviour
{
    public UnityEngine.Video.VideoPlayer videoPlayer;
    public GameObject videoScreen;
    public GameObject descriptionPanel;
    public TextMeshProUGUI descriptionTextUI;
    public GameObject frameGuide;
    public QuizManager quizManager;

    private string currentJobId;
    private string latestDescriptionText = "";
    private string lastFinalVideoPath = ""; // ✨ [신규] 마지막 최종 영상 경로 저장용 변수

    void Start()
    {
        if (videoScreen != null)
            videoScreen.SetActive(false);

        if (videoPlayer != null)
        {
            videoPlayer.loopPointReached -= OnVideoEnd;
            videoPlayer.loopPointReached += OnVideoEnd;
            videoPlayer.isLooping = false;
        }

        if (descriptionPanel != null)
            descriptionPanel.SetActive(false);
    }

    public void SendImageForVideo(Texture2D image, Vector3 worldPos)
    {
        if (image == null) return;
        if (frameGuide != null) frameGuide.SetActive(false);
        if (descriptionPanel != null) descriptionPanel.SetActive(false);

        StopAllCoroutines();
        // ✨ 새 작업 시작 시 마지막 영상 경로 초기화
        lastFinalVideoPath = "";

        byte[] imageData = image.EncodeToJPG();
        StartCoroutine(StartFullSequence(imageData, worldPos));
    }

    private IEnumerator StartFullSequence(byte[] imageData, Vector3 worldPos)
    {
        string preprocessUrl = "http://211.180.114.54:5058/preprocess";
        var form = new WWWForm();
        form.AddBinaryData("image", imageData, "captured.jpg", "image/jpeg");

        // 별명과 함께 미술관 이름도 폼에 추가
        string userNickname = PlayerPrefs.GetString("nickname", "친구");
        string museumName = PlayerPrefs.GetString("museum_name", ""); // ✨ [추가] 미술관 이름 불러오기

        form.AddField("nickname", userNickname);
        form.AddField("museum_name", museumName); // ✨ [추가] 폼에 필드 추가

        Debug.Log($"서버로 전송: 닉네임='{userNickname}', 장소='{museumName}'");

        // 이하 로직은 동일...
        UnityWebRequest preReq = UnityWebRequest.Post(preprocessUrl, form);
        yield return preReq.SendWebRequest();

        if (preReq.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("전처리 실패: " + preReq.error);
            yield break;
        }

        // 이하 로직은 동일...
        JobIdResponse jobResponse = JsonUtility.FromJson<JobIdResponse>(preReq.downloadHandler.text);
        currentJobId = jobResponse.job_id;
        Debug.Log($"✅ Preprocess 성공! Job ID: {currentJobId}");

        Debug.Log("--- 1. 인사 영상 단계 시작 ---");
        yield return StartCoroutine(PollAndPlayVideo(currentJobId, "get-greet-video", worldPos, false));

        Debug.Log("--- 2. 퀴즈 단계 시작 ---");
        yield return StartCoroutine(GetDescriptionAndShowQuiz(currentJobId));
    }

    private IEnumerator PollAndPlayVideo(string jobId, string endpoint, Vector3 position, bool isFinalStep)
    {
        string url = $"http://211.180.114.54:5058/{endpoint}?job_id={jobId}";
        Debug.Log($"Polling URL: {url}");
        float pollStartTime = Time.time;
        float maxWaitTime = isFinalStep ? 60f : 40f;
        while (Time.time - pollStartTime < maxWaitTime)
        {
            UnityWebRequest req = UnityWebRequest.Get(url);
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                Debug.Log($"✅ 영상 다운로드 성공: {endpoint}");
                string videoPath = SaveTempFile(req.downloadHandler.data, $"{endpoint}.mp4");

                // ✨ [수정] 최종 영상일 경우, 경로를 저장합니다.
                if (isFinalStep)
                {
                    lastFinalVideoPath = videoPath;
                    Debug.Log($"최종 영상 경로 저장됨: {lastFinalVideoPath}");
                }

                yield return StartCoroutine(PlayVideoFromFile(videoPath, position));
                Debug.Log($"✅ 영상 재생 완료: {endpoint}");
                if (isFinalStep)
                {
                    Debug.Log("모든 시퀀스 완료! 액자를 다시 표시합니다.");
                    if (frameGuide != null) frameGuide.SetActive(true);
                }
                yield break;
            }
            else if (req.responseCode == 404)
            {
                Debug.Log($"영상 준비 중... 1초 후 재시도 ({endpoint})");
                yield return new WaitForSeconds(1f);
            }
            else
            {
                Debug.LogError($"영상 폴링 에러 ({endpoint}): {req.error}");
                if (frameGuide != null) frameGuide.SetActive(true);
                yield break;
            }
        }
        Debug.LogWarning($"영상 폴링 최대 대기 시간 초과! ({endpoint})");
        if (frameGuide != null) frameGuide.SetActive(true);
    }

    private IEnumerator GetDescriptionAndShowQuiz(string jobId)
    {
        string url = $"http://211.180.114.54:5058/get-description?job_id={jobId}";
        UnityWebRequest req = UnityWebRequest.Get(url);
        yield return req.SendWebRequest();
        if (req.result == UnityWebRequest.Result.Success)
        {
            GptResponse resp = JsonUtility.FromJson<GptResponse>(req.downloadHandler.text);
            latestDescriptionText = resp.result;
            if (quizManager != null && !string.IsNullOrEmpty(resp.artist))
            {
                Debug.Log($"✅ 설명 다운로드 성공. 아티스트: {resp.artist}. 퀴즈를 표시합니다.");
                quizManager.ShowQuiz(resp.artist);
            }
        }
        else
        {
            Debug.LogError("설명 다운로드 에러: " + req.error);
            latestDescriptionText = "설명을 불러오는 데 실패했습니다.";
            if (frameGuide != null) frameGuide.SetActive(true);
        }
    }

    public void OnQuizCompleted()
    {
        Debug.Log("--- 3. 최종 영상 단계 시작 ---");
        if (quizManager != null) quizManager.quizPanel.SetActive(false);
        Vector3 lastVideoPosition = videoScreen.transform.position;
        StartCoroutine(PollAndPlayVideo(currentJobId, "get-final-video", lastVideoPosition, true));
    }

    private IEnumerator PlayVideoFromFile(string filePath, Vector3 position)
    {
        if (videoPlayer == null || videoScreen == null) yield break;
        videoPlayer.source = UnityEngine.Video.VideoSource.Url;
        videoPlayer.url = "file://" + filePath;
        videoScreen.SetActive(true);
        videoPlayer.Prepare();
        while (!videoPlayer.isPrepared) yield return null;
        videoScreen.transform.position = position;
        Vector3 lookAt = Camera.main.transform.position;
        lookAt.y = videoScreen.transform.position.y;
        videoScreen.transform.LookAt(lookAt);
        videoScreen.transform.localScale = new Vector3(1.3f * (9f / 16f), 1.3f, 1f);
        videoPlayer.Play();
        while (videoPlayer.isPlaying) yield return null;
        videoScreen.SetActive(false);
    }

    private void OnVideoEnd(UnityEngine.Video.VideoPlayer vp)
    {
        Debug.Log($"OnVideoEnd 콜백 호출됨: {vp.url}");
    }

    private string SaveTempFile(byte[] bytes, string filename)
    {
        string path = Path.Combine(Application.persistentDataPath, filename);
        File.WriteAllBytes(path, bytes);
        return path;
    }

    public void ToggleDescription()
    {
        if (descriptionPanel == null || descriptionTextUI == null) return;
        if (videoPlayer.isPlaying || (quizManager != null && quizManager.quizPanel.activeSelf))
        {
            Debug.Log("영상 재생 또는 퀴즈 진행 중에는 설명을 볼 수 없습니다.");
            return;
        }
        bool isPanelActive = descriptionPanel.activeSelf;
        descriptionPanel.SetActive(!isPanelActive);
        if (!isPanelActive)
        {
            descriptionTextUI.text = latestDescriptionText;
            if (frameGuide != null) frameGuide.SetActive(false);
        }
        else
        {
            if (frameGuide != null) frameGuide.SetActive(true);
        }
    }

    // ✨ [신규] 마지막 최종 영상을 다시 재생하는 함수
    public void ReplayFinalVideo()
    {
        // 다른 작업이 진행 중이 아닐 때만 재생
        if (videoPlayer.isPlaying || (quizManager != null && quizManager.quizPanel.activeSelf))
        {
            Debug.Log("다른 작업 진행 중에는 다시보기를 할 수 없습니다.");
            return;
        }

        if (string.IsNullOrEmpty(lastFinalVideoPath))
        {
            Debug.LogWarning("다시 재생할 영상이 없습니다.");
            return;
        }

        Debug.Log($"최종 영상 다시 재생: {lastFinalVideoPath}");
        StartCoroutine(ReplayFinalVideoCoroutine());
    }

    // ✨ [신규] 다시 재생을 위한 코루틴
    private IEnumerator ReplayFinalVideoCoroutine()
    {
        if (frameGuide != null) frameGuide.SetActive(false); // 액자 숨기기

        // 저장된 경로와 마지막 위치를 사용해 영상 재생
        yield return StartCoroutine(PlayVideoFromFile(lastFinalVideoPath, videoScreen.transform.position));

        if (frameGuide != null) frameGuide.SetActive(true); // 끝나면 액자 다시 표시
    }

    // --- JSON 응답을 위한 클래스들 ---
    [System.Serializable] public class JobIdResponse { public string job_id; }
    [System.Serializable]
    public class GptResponse
    {
        public string result;
        public string profile;
        public string audio_path;
        public string artist;
    }
}