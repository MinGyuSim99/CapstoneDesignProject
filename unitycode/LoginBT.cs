// LoginBT 최종 수정본
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using UnityEngine.SceneManagement;
using UnityEngine.Networking;
using System.Collections;

public class LoginBT : MonoBehaviour
{
    [SerializeField] TMP_InputField nicknameInput;
    [SerializeField] TMP_InputField museumInput; // ✨ [추가] 미술관 입력칸을 연결할 변수
    [SerializeField] Button loginButton;

    const string GREET_API = "http://211.180.114.54:5058/create-greet";

    void Start()
    {
        loginButton.onClick.AddListener(OnLoginClicked);
    }

    void OnLoginClicked()
    {
        string nick = nicknameInput.text.Trim();
        string museum = museumInput.text.Trim(); // ✨ [추가] 미술관 입력칸의 텍스트를 가져옵니다.

        if (string.IsNullOrEmpty(nick))
        {
            Debug.LogWarning("⚠️ 별명을 입력해 주세요!");
            return;
        }

        // 1) 로컬 저장소(PlayerPrefs)에 별명과 미술관 이름을 저장합니다.
        PlayerPrefs.SetString("nickname", nick);
        PlayerPrefs.SetString("museum_name", museum); // ✨ [추가] 미술관 이름을 저장합니다.
        Debug.Log($"✅ 정보 저장 완료: 별명='{nick}', 장소='{museum}'");

        // 2) 서버에 인사 TTS 생성을 요청합니다 (백그라운드에서 실행됨).
        StartCoroutine(RequestGreetTTS(nick));

        // 3) 모든 준비가 끝났으므로, 바로 AR 씬으로 전환합니다.
        SceneManager.LoadScene("SampleScene");   // ← 실제 AR 씬 이름으로 변경 필요
    }

    IEnumerator RequestGreetTTS(string nick)
    {
        WWWForm form = new WWWForm();
        form.AddField("nickname", nick);

        using UnityWebRequest www = UnityWebRequest.Post(GREET_API, form);
        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
            Debug.LogWarning($"❌ Greet TTS 생성 실패: {www.error}");
        else
            Debug.Log("✅ Greet TTS 준비 요청 완료");
    }
}