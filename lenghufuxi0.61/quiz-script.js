// 全局变量
let isLoggedIn = false;
let currentUser = null;
let currentScore = 0;
let totalScore = 0;
let currentQuestionIndex = 0;
let questions = [];
let userAnswers = [];
let startTime = 0;
let timerInterval = null;
let selectedKnowledge = null;
let chapters = [];
let selectedChapter = null;
let selectedFirstLevelChapter = null;
let selectedSecondLevelChapter = null;
let USER_NAME = '匿名用户';

// API基础URL由quiz-system.html定义

// DOM元素变量
let loginSection, registerSection, knowledgeSection, quizSection, resultSection, rankingSection, knowledgeManagementSection, chapterManagementSection, chapterSelectionSection;
let loginBtn, registerBtn, goToRegisterBtn, goToLoginBtn, rankingBtn, backBtn, clearRankingsBtn, prevBtn, nextBtn, submitBtn, restartBtn;
let manageChaptersBtn, addLevel1ChapterBtn, viewChaptersBtn, backToChapterMainBtn, backToChapterListBtn, saveChapterBtn, cancelChapterEditBtn;
let manageKnowledgeBtn, selectChapterBtn, backFromChapterSelectionBtn, backFromLessonSelectionBtn, firstLevelChapterSelect, secondLevelChapterSelect;
let addKnowledgeBtn, saveKnowledgeBtn, cancelEditBtn, showNetworkAddressBtn, hostManagementBtn, backToMainFromHostBtn, backToMainFromChapterBtn, backToMainBtn;
let savePermissionsBtn, cancelPermissionsBtn;
let userNameInput, knowledgeItems, startBtn, adminControls, knowledgeList, knowledgeForm, formTitle, knowledgeId, knowledgeTitle, knowledgeContent, knowledgeCategory, knowledgeImage, knowledgeChapter, knowledgeChapterEdit;
let questionText, optionsContainer, questionCount, timerElement, totalQuestionsElement, correctAnswersElement, accuracyElement, totalTimeElement, currentScoreElement, totalScoreElement, myTotalScoreElement, rankingListElement, rankingListFullElement;

// 初始化DOM元素
function initDOMElements() {
    // 登录注册相关
    loginSection = document.getElementById('login-section');
    registerSection = document.getElementById('register-section');
    loginBtn = document.getElementById('login-btn');
    registerBtn = document.getElementById('register-btn');
    goToRegisterBtn = document.getElementById('go-to-register');
    goToLoginBtn = document.getElementById('go-to-login');
    
    // 主界面相关
    knowledgeSection = document.getElementById('knowledge-section');
    quizSection = document.getElementById('quiz-section');
    resultSection = document.getElementById('result-section');
    rankingSection = document.getElementById('ranking-section');
    knowledgeManagementSection = document.getElementById('knowledge-management-section');
    chapterManagementSection = document.getElementById('chapter-management-section');
    chapterSelectionSection = document.getElementById('chapter-selection-section');
    
    // 按钮相关
    knowledgeItems = document.querySelectorAll('.knowledge-item');
    startBtn = document.getElementById('start-btn');
    rankingBtn = document.getElementById('ranking-btn');
    backBtn = document.getElementById('back-btn');
    clearRankingsBtn = document.getElementById('clear-rankings-btn');
    adminControls = document.getElementById('admin-controls');
    manageKnowledgeBtn = document.getElementById('manage-knowledge-btn');
    manageChaptersBtn = document.getElementById('manage-chapters-btn');
    addKnowledgeBtn = document.getElementById('add-knowledge-btn');
    backToMainBtn = document.getElementById('back-to-main-btn');
    
    // 知识库相关
    knowledgeList = document.getElementById('knowledge-list');
    knowledgeForm = document.getElementById('knowledge-form');
    formTitle = document.getElementById('form-title');
    knowledgeId = document.getElementById('knowledge-id');
    knowledgeTitle = document.getElementById('knowledge-title');
    knowledgeContent = document.getElementById('knowledge-content');
    knowledgeCategory = document.getElementById('knowledge-category');
    knowledgeImage = document.getElementById('knowledge-image');
    knowledgeChapter = document.getElementById('knowledge-chapter');
    knowledgeChapterEdit = document.getElementById('knowledge-chapter-edit');
    saveKnowledgeBtn = document.getElementById('save-knowledge-btn');
    cancelEditBtn = document.getElementById('cancel-edit-btn');
    
    // 答题相关
    questionText = document.getElementById('question-text');
    optionsContainer = document.getElementById('options-container');
    questionCount = document.getElementById('question-count');
    timerElement = document.getElementById('timer');
    prevBtn = document.getElementById('prev-btn');
    nextBtn = document.getElementById('next-btn');
    submitBtn = document.getElementById('submit-btn');
    restartBtn = document.getElementById('restart-btn');
    totalQuestionsElement = document.getElementById('total-questions');
    correctAnswersElement = document.getElementById('correct-answers');
    accuracyElement = document.getElementById('accuracy');
    totalTimeElement = document.getElementById('total-time');
    currentScoreElement = document.getElementById('current-score');
    totalScoreElement = document.getElementById('total-score-value');
    myTotalScoreElement = document.getElementById('my-total-score');
    rankingListElement = document.getElementById('ranking-list');
    rankingListFullElement = document.getElementById('ranking-list-full');
    
    // 章节管理相关
    addLevel1ChapterBtn = document.getElementById('add-level1-chapter-btn');
    viewChaptersBtn = document.getElementById('view-chapters-btn');
    backToChapterMainBtn = document.getElementById('back-to-chapter-main');
    backToChapterListBtn = document.getElementById('back-to-chapter-list');
    saveChapterBtn = document.getElementById('save-chapter-btn');
    cancelChapterEditBtn = document.getElementById('cancel-chapter-edit-btn');
    
    // 章节选择相关
    selectChapterBtn = document.getElementById('select-chapter-btn');
    backFromChapterSelectionBtn = document.getElementById('back-from-chapter-selection');
    backFromLessonSelectionBtn = document.getElementById('back-from-lesson-selection');
    firstLevelChapterSelect = document.getElementById('first-level-chapter');
    secondLevelChapterSelect = document.getElementById('second-level-chapter');
    
    // 其他按钮
    showNetworkAddressBtn = document.getElementById('show-network-address-btn');
    hostManagementBtn = document.getElementById('host-management-btn');
    backToMainFromHostBtn = document.getElementById('back-to-main-from-host');
    backToMainFromChapterBtn = document.getElementById('back-to-main-from-chapter');
    savePermissionsBtn = document.getElementById('save-permissions-btn');
    cancelPermissionsBtn = document.getElementById('cancel-permissions-btn');
    
    // 用户名输入
    userNameInput = document.getElementById('user-name');
}

// 生成或获取用户名字
function initUser() {
    // 从本地存储获取用户名字
    const storedName = localStorage.getItem('quizUserName');
    if (storedName) {
        USER_NAME = storedName;
        if (userNameInput) {
            userNameInput.value = storedName;
        }
    } else {
        // 默认用户名
        USER_NAME = '匿名用户';
    }
}

// 更新用户名字
function updateUserName() {
    if (userNameInput) {
        const inputName = userNameInput.value.trim();
        if (inputName) {
            USER_NAME = inputName;
            localStorage.setItem('quizUserName', inputName);
        } else {
            USER_NAME = '匿名用户';
            localStorage.removeItem('quizUserName');
        }
    }
}

// 初始化积分数据
function initScoreData() {
    // 从本地存储获取总分
    const storedScore = localStorage.getItem('quizTotalScore');
    if (storedScore) {
        totalScore = parseInt(storedScore);
    } else {
        totalScore = 0;
    }
}

// 初始化事件监听
function initEventListeners() {
    // 登录注册事件监听
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
    }
    if (registerBtn) {
        registerBtn.addEventListener('click', handleRegister);
    }
    if (goToRegisterBtn) {
        goToRegisterBtn.addEventListener('click', () => {
            switchSection('register');
        });
    }
    if (goToLoginBtn) {
        goToLoginBtn.addEventListener('click', () => {
            switchSection('login');
        });
    }
    
    // 查看排行榜 - 先更新用户名
    if (rankingBtn) {
        rankingBtn.addEventListener('click', () => {
            updateUserName();
            showRankingPage();
        });
    }
    
    // 返回主界面
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            switchSection('knowledge');
        });
    }
    
    // 清空排行榜
    if (clearRankingsBtn) {
        clearRankingsBtn.addEventListener('click', clearRankings);
    }
    
    // 上一题
    if (prevBtn) {
        prevBtn.addEventListener('click', prevQuestion);
    }
    
    // 下一题
    if (nextBtn) {
        nextBtn.addEventListener('click', nextQuestion);
    }
    
    // 提交答案
    if (submitBtn) {
        submitBtn.addEventListener('click', submitQuiz);
    }
    
    // 重新开始
    if (restartBtn) {
        restartBtn.addEventListener('click', restartQuiz);
    }
    
    // 注销功能
    const logoutBtns = [
        document.getElementById('logout-btn'),
        document.getElementById('logout-btn-km'),
        document.getElementById('logout-btn-ranking'),
        document.getElementById('logout-btn-quiz'),
        document.getElementById('logout-btn-result')
    ];
    
    logoutBtns.forEach(btn => {
        if (btn) {
            btn.addEventListener('click', handleLogout);
        }
    });
    
    // 章节管理事件监听
    if (manageChaptersBtn) {
        manageChaptersBtn.addEventListener('click', () => {
            switchSection('chapter-management');
            loadChapters();
        });
    }
    
    // 章节管理界面按钮事件监听
    if (addLevel1ChapterBtn) {
        addLevel1ChapterBtn.addEventListener('click', () => {
            document.getElementById('chapter-id').value = '';
            document.getElementById('chapter-name').value = '';
            document.getElementById('parent-chapter').value = '';
            document.getElementById('chapter-form-title').textContent = '添加课程';
            document.getElementById('chapter-main-view').style.display = 'none';
            document.getElementById('chapter-list-view').style.display = 'none';
            document.getElementById('chapter-edit-view').style.display = 'block';
            document.getElementById('parent-chapter-group').style.display = 'block';
        });
    }
    
    if (viewChaptersBtn) {
        viewChaptersBtn.addEventListener('click', () => {
            document.getElementById('chapter-main-view').style.display = 'none';
            document.getElementById('chapter-list-view').style.display = 'block';
            loadChapters();
        });
    }
    
    if (backToChapterMainBtn) {
        backToChapterMainBtn.addEventListener('click', () => {
            document.getElementById('chapter-list-view').style.display = 'none';
            document.getElementById('chapter-main-view').style.display = 'block';
        });
    }
    
    if (backToChapterListBtn) {
        backToChapterListBtn.addEventListener('click', () => {
            document.getElementById('chapter-edit-view').style.display = 'none';
            document.getElementById('chapter-list-view').style.display = 'block';
            document.getElementById('chapter-main-view').style.display = 'none';
        });
    }
    
    if (saveChapterBtn) {
        saveChapterBtn.addEventListener('click', saveChapter);
    }
    
    if (cancelChapterEditBtn) {
        cancelChapterEditBtn.addEventListener('click', () => {
            document.getElementById('chapter-edit-view').style.display = 'none';
            document.getElementById('chapter-list-view').style.display = 'block';
            document.getElementById('chapter-main-view').style.display = 'none';
        });
    }
    
    // 知识库管理事件监听
    if (manageKnowledgeBtn) {
        manageKnowledgeBtn.addEventListener('click', () => {
            switchSection('knowledge-management');
            loadChaptersForKnowledgeManagement();
            loadKnowledgeBase();
        });
    }
    
    // 章节选择事件监听
    if (selectChapterBtn) {
        selectChapterBtn.addEventListener('click', () => {
            switchSection('chapter-selection');
            loadFirstLevelChapters();
        });
    }
    
    // 课程选择界面返回按钮事件监听
    if (backFromChapterSelectionBtn) {
        backFromChapterSelectionBtn.addEventListener('click', () => {
            switchSection('knowledge');
        });
    }
    
    // 课程选择界面返回按钮事件监听
    if (backFromLessonSelectionBtn) {
        backFromLessonSelectionBtn.addEventListener('click', () => {
            switchSection('chapter-selection');
        });
    }
    
    // 一级章节选择事件监听
    if (firstLevelChapterSelect) {
        firstLevelChapterSelect.addEventListener('change', async () => {
            const selectedChapterId = parseInt(firstLevelChapterSelect.value);
            await loadSecondLevelCoursesForKnowledgeManagement(selectedChapterId);
        });
    }
    
    // 二级课程选择事件监听
    if (secondLevelChapterSelect) {
        secondLevelChapterSelect.addEventListener('change', () => {
            const selectedCourseId = parseInt(secondLevelChapterSelect.value);
            loadKnowledgeByChapter(selectedCourseId);
        });
    }
    
    // 添加知识点事件监听
    if (addKnowledgeBtn) {
        addKnowledgeBtn.addEventListener('click', () => {
            showKnowledgeForm();
        });
    }
    
    // 保存知识点事件监听
    if (saveKnowledgeBtn) {
        saveKnowledgeBtn.addEventListener('click', saveKnowledge);
    }
    
    // 取消编辑知识点事件监听
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', hideKnowledgeForm);
    }
    
    // 查看网络访问地址事件监听
    if (showNetworkAddressBtn) {
        showNetworkAddressBtn.addEventListener('click', showNetworkAccessAddress);
    }
    
    // 主机管理事件监听
    if (hostManagementBtn) {
        hostManagementBtn.addEventListener('click', () => {
            switchSection('host-management');
            loadUserList();
        });
    }
    
    // 主机管理返回事件监听
    if (backToMainFromHostBtn) {
        backToMainFromHostBtn.addEventListener('click', () => {
            switchSection('knowledge');
        });
    }
    
    // 章节管理返回事件监听
    if (backToMainFromChapterBtn) {
        backToMainFromChapterBtn.addEventListener('click', () => {
            switchSection('knowledge');
        });
    }
    
    // 知识库管理返回事件监听
    if (backToMainBtn) {
        backToMainBtn.addEventListener('click', () => {
            switchSection('knowledge');
        });
    }
    
    // 保存权限事件监听
    if (savePermissionsBtn) {
        savePermissionsBtn.addEventListener('click', saveCoursePermissions);
    }
    
    // 取消权限管理事件监听
    if (cancelPermissionsBtn) {
        cancelPermissionsBtn.addEventListener('click', () => {
            document.getElementById('course-permission-container').style.display = 'none';
            document.querySelector('.user-list-container').style.display = 'block';
        });
    }
}

// 初始化
function init() {
    initDOMElements();
    initUser();
    initScoreData();
    initEventListeners();
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', init);
