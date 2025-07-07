using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class QuizManager : MonoBehaviour
{
    public GameObject quizPanel;
    public Button[] optionButtons;

    private string correctArtist;
    private int correctIndex;

    private Dictionary<Button, Color> originalColors = new Dictionary<Button, Color>();

    private List<string> allArtists = new List<string> {
        "레오나르도 다 빈치", "빈센트 반 고흐", "클로드 모네", "파블로 피카소",
        "프리다 칼로", "에드바르 뭉크", "폴 세잔", "산드로 보티첼리", "장 프랑수아 밀레"
    };

    public void ShowQuiz(string correctArtistName)
    {
        quizPanel.SetActive(true);
        correctArtist = correctArtistName;

        var candidates = allArtists.Where(x => x != correctArtist).OrderBy(x => Random.value).Take(3).ToList();
        candidates.Add(correctArtist);
        candidates = candidates.OrderBy(x => Random.value).ToList();
        correctIndex = candidates.IndexOf(correctArtist);

        for (int i = 0; i < optionButtons.Length; i++)
        {
            int index = i;
            var btn = optionButtons[i];
            btn.GetComponentInChildren<TextMeshProUGUI>().text = candidates[i];

            var img = btn.GetComponent<Image>();
            if (!originalColors.ContainsKey(btn))
                originalColors[btn] = img.color;

            btn.onClick.RemoveAllListeners();
            btn.onClick.AddListener(() => OnSelect(index));
        }
    }

    private void OnSelect(int selectedIndex)
    {
        if (selectedIndex == correctIndex)
        {
            OnCorrectAnswer();
        }
        else
        {
            OnWrongAnswer(selectedIndex);
        }

        foreach (var btn in optionButtons)
            btn.interactable = false;

        // ✨ [추가] 퀴즈가 끝나고 패널이 사라지기 전에, ImageSender에 다음 단계 진행 신호 보내기
        ImageSender imageSender = FindObjectOfType<ImageSender>();
        if (imageSender != null)
        {
            // 이 시점에 최종 영상 로딩이 시작됩니다.
            imageSender.OnQuizCompleted();
        }
        else
        {
            Debug.LogError("ImageSender를 찾을 수 없습니다!");
        }

        // 2초 후에 퀴즈 패널 숨기기
        Invoke("HideQuiz", 2f);
    }

    private void OnCorrectAnswer()
    {
        Debug.Log("정답! 🎉");
        for (int i = 0; i < optionButtons.Length; i++)
        {
            var img = optionButtons[i].GetComponent<Image>();
            img.color = (i == correctIndex) ? new Color(0.6f, 1f, 0.6f) : originalColors[optionButtons[i]];
        }
    }

    private void OnWrongAnswer(int selectedIndex)
    {
        Debug.Log("오답 ❌");
        for (int i = 0; i < optionButtons.Length; i++)
        {
            var img = optionButtons[i].GetComponent<Image>();
            img.color = (i == correctIndex) ? new Color(0.6f, 1f, 0.6f) :
                        (i == selectedIndex) ? new Color(1f, 0.6f, 0.6f) : originalColors[optionButtons[i]];
        }
    }

    private void HideQuiz()
    {
        foreach (var btn in optionButtons)
        {
            btn.interactable = true;
            if (originalColors.ContainsKey(btn))
                btn.GetComponent<Image>().color = originalColors[btn];
        }
        quizPanel.SetActive(false);
    }
}