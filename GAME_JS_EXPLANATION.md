# 🎨 HƯỚNG DẪN CHI TIẾT CÁC HÀM, HỘP THOẠI (PROMPTS/MODALS) VÀ LOGIC TRONG `game.js`

File [game.js](file:///Users/nguyenbaongoc/Documents/millionaire/static/js/game.js) là **"trái tim"** điều khiển toàn bộ giao diện trò chơi ở phía Client (Trình duyệt). File này quản lý trạng thái trò chơi, xử lý các sự kiện click, thực hiện các cuộc gọi API không đồng bộ đến server Flask, vẽ vòng đếm ngược SVG, tạo hiệu ứng pháo hoa giấy (confetti) và đặc biệt là tự động tổng hợp âm thanh bằng code.

Dưới đây là hướng dẫn chi tiết từng bước, cấu trúc biến, hàm và hộp thoại (Modals/Prompts) trong file để bạn dễ học tập.

---

## 🗺️ TỔNG QUAN CÁC BIẾN TRẠNG THÁI (STATE VARIABLES)

Ở đầu file, hệ thống định nghĩa các biến toàn cục để lưu trữ trạng thái hiện tại của game:
```javascript
let sessionId = '';           // ID phiên chơi duy nhất được cấp từ Backend khi bắt đầu game
let playerName = '';          // Tên người chơi nhập vào
let currentQuestion = 0;      // Chỉ số câu hỏi hiện tại (từ 0 đến 14, tương ứng câu 1 đến 15)
let timer = null;             // Tham chiếu đến bộ đếm thời gian (setInterval)
let timeLeft = 30;            // Số giây còn lại cho câu hỏi hiện tại (giảm từ 30 về 0)
let isAnswered = false;       // Cờ đánh dấu người chơi đã bấm chọn đáp án chưa (tránh click nhiều lần)
let soundEnabled = true;      // Trạng thái bật/tắt âm thanh
let chatbotOpen = false;      // Trạng thái hiển thị khung chat với MC Trợ lý ảo
```

---

## 1. 🚀 KHỞI ĐỘNG GAME & KHỞI TẠO BAN ĐẦU

### A. Sự kiện DOMContentLoaded
```javascript
document.addEventListener('DOMContentLoaded', () => {
    createParticles();    // Tạo hiệu ứng hạt bay lung linh ở nền
    buildMoneyLadder();   // Dựng cột tiền thưởng 15 mốc bên phải màn hình
    addBotMessage("Xin chào! 👋 Tôi là MC Trợ Lý. Chúc bạn may mắn nhé!");
});
```
*   `DOMContentLoaded`: Sự kiện kích hoạt khi trình duyệt đã tải xong cấu trúc HTML của trang web, đảm bảo các hàm gọi phần tử DOM (như `document.getElementById`) sẽ không bị lỗi `null`.

### B. Hàm Bắt Đầu Game (`startGame`)
Hàm này chạy khi người dùng nhấn nút "Bắt đầu chơi".
```javascript
async function startGame() {
    playerName = document.getElementById('player-name').value.trim() || 'Người chơi';
    
    // Đổi nút bấm sang trạng thái đang tải câu hỏi (chờ Gemini AI tạo câu hỏi)
    const btn = document.getElementById('start-btn');
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ĐANG VÀO GAME XIN CHỜ MỘT CHÚT';
    btn.disabled = true;
    btn.style.opacity = '0.7';

    try {
        // Gửi request POST tới server Flask để bắt đầu phiên chơi mới
        const res = await fetch(API_URL + '/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: playerName })
        });
        const data = await res.json();

        if (data.success) {
            sessionId = data.session_id; // Lưu lại ID phiên chơi
            currentQuestion = 0;
            isAnswered = false;

            switchScreen('game-screen'); // Chuyển giao diện từ màn hình chờ sang màn hình chơi
            displayQuestion(data.question, data.question_number); // Hiển thị câu hỏi số 1
        } else {
            // Xử lý khi hết lượt chơi hoặc lỗi hệ thống
            if (data.error && data.error.includes('hết lượt chơi')) {
                // Hiển thị hộp thoại (modal) thông báo hết lượt chơi và đề xuất vào Shop
                showModal('HẾT LƯỢT CHƠI 🎮', `
                    <p>Bạn đã sử dụng hết lượt chơi miễn phí. Hãy ghé qua cửa hàng nhé!</p>
                    <button class="btn-start" onclick="closeModal(); openShop();">🛒 GHÉ CỬA HÀNG</button>
                `);
            } else {
                alert('⚠️ Lỗi: ' + data.error);
            }
        }
    } catch (err) {
        alert('❌ Không thể kết nối tới server!');
    } finally {
        // Khôi phục trạng thái nút bấm ban đầu
        btn.innerHTML = oldHtml;
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}
```

---

## 2. ⏱️ ĐỒNG HỒ ĐẾM NGƯỢC & HIỆU ỨNG VÒNG TRÒN SVG

Mỗi câu hỏi có **30 giây** để suy nghĩ. Logic này được điều khiển bởi các hàm:

### A. Hàm Chạy Đồng Hồ (`startTimer`)
```javascript
function startTimer() {
    timeLeft = 30;
    clearInterval(timer); // Xóa bộ đếm cũ nếu có để tránh đếm nhanh gấp đôi
    updateTimerDisplay();
    timer = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        if (timeLeft <= 0) {
            clearInterval(timer);
            timeUp(); // Gọi hàm xử lý khi hết giờ
        }
    }, 1000); // Lặp lại sau mỗi 1000 mili-giây (1 giây)
}
```

### B. Hàm Cập Nhật Hiệu Ứng Vòng Tròn (`updateTimerDisplay`)
```javascript
function updateTimerDisplay() {
    document.getElementById('timer-text').textContent = timeLeft;
    const circle = document.getElementById('timer-circle');
    
    // Tính toán độ dài nét viền bị ẩn đi (strokeDashoffset)
    // 283 là chu vi chuẩn của vòng tròn vẽ trong HTML: 2 * PI * r = 2 * 3.14 * 45 ≈ 283
    circle.style.strokeDashoffset = 283 - (283 * timeLeft) / 30;

    // Đổi màu vòng tròn sang đỏ khi sắp hết giờ để tăng sự kịch tính
    circle.classList.remove('warning', 'danger');
    if (timeLeft <= 5) {
        circle.classList.add('danger'); // Đỏ nhấp nháy
        playSound('tick');              // Tiếng tíc tắc cảnh báo
    } else if (timeLeft <= 10) {
        circle.classList.add('warning'); // Cam
    }
}
```

---

## 3. 🎯 LỰA CHỌN ĐÁP ÁN & ĐỘ TRỄ KỊCH TÍNH

Khi người chơi bấm vào 1 trong 4 ô đáp án, hàm `selectAnswer(index)` sẽ được thực thi.

```javascript
async function selectAnswer(index) {
    if (isAnswered) return; // Nếu đã bấm rồi thì bỏ qua, tránh spam click
    isAnswered = true;
    clearInterval(timer); // Dừng đồng hồ đếm ngược lại ngay lập tức

    // Tô màu vàng (Trạng thái Đang Chọn - Selected) cho ô đáp án vừa bấm
    const selectedBtn = document.getElementById('answer-' + index);
    selectedBtn.classList.add('selected');
    
    // Phát âm thanh hồi hộp chờ đợi
    playSound('select');

    // Tạo độ trễ kịch tính 2 giây trước khi công bố đáp án giống như trên TV
    setTimeout(async () => {
        try {
            // Gửi đáp án lên backend kiểm tra
            const res = await fetch(API_URL + '/api/game/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    selected_answer: index
                })
            });
            const data = await res.json();

            if (data.success) {
                // Loại bỏ màu vàng lựa chọn
                selectedBtn.classList.remove('selected');

                if (data.is_correct) {
                    // TRẢ LỜI ĐÚNG:
                    selectedBtn.classList.add('correct'); // Tô màu xanh lá (Correct)
                    playSound('right');                   // Tiếng chuông đúng
                    createConfetti();                     // Pháo hoa giấy bay tung tóe
                    
                    // Cập nhật mốc câu hiện tại
                    currentQuestion = data.next_question_number - 1;

                    // Chờ 2 giây để người chơi ăn mừng rồi tự chuyển câu tiếp theo
                    setTimeout(() => {
                        if (data.game_over && data.result === 'win') {
                            showResult(false, true, data); // Thắng cuộc hoàn toàn (vượt qua câu 15)
                        } else {
                            displayQuestion(data.question, data.next_question_number);
                        }
                    }, 2000);
                } else {
                    // TRẢ LỜI SAI:
                    selectedBtn.classList.add('wrong'); // Tô màu đỏ (Wrong) cho đáp án đã chọn
                    // Tô sáng đáp án đúng thực tế để người chơi biết mình sai ở đâu
                    document.getElementById('answer-' + data.correct_answer).classList.add('correct');
                    playSound('wrong'); // Tiếng còi báo sai
                    
                    setTimeout(() => {
                        showResult(false, false, data); // Chuyển sang màn hình Thất Bại
                    }, 2000);
                }
            }
        } catch (err) {
            alert('⚠️ Lỗi kiểm tra đáp án!');
            isAnswered = false;
        }
    }, 2000); // 2000ms = 2 giây kịch tính
}
```

---

## 4. ☎️ SỬ DỤNG QUYỀN TRỢ GIÚP (LIFELINES)

Hàm `useLifeline(type)` xử lý 3 quyền trợ giúp gửi yêu cầu lên Backend:

```javascript
async function useLifeline(type) {
    if (isAnswered) return; // Không cho phép trợ giúp nếu đã chọn đáp án hoặc hết giờ

    const btn = document.getElementById('lifeline-' + type);
    if (btn.classList.contains('used')) return; // Tránh bấm lại quyền đã dùng

    try {
        const res = await fetch(API_URL + '/api/game/lifeline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, lifeline_type: type })
        });
        const data = await res.json();

        if (data.success) {
            btn.classList.add('used'); // Đánh dấu đã dùng quyền trợ giúp này (làm mờ nút)
            playSound('assist');       // Phát âm thanh dùng trợ giúp

            if (type === '5050') {
                // Trợ giúp 50/50: Ẩn đi 2 đáp án sai
                data.removed_answers.forEach(idx => {
                    document.getElementById('answer-' + idx).style.display = 'none';
                });
            } 
            else if (type === 'audience') {
                // Trợ giúp khảo sát ý kiến khán giả: Dựng biểu đồ phần trăm
                let pollHtml = '<div style="display:flex; justify-content:space-around; align-items:flex-end; height:150px; padding-top:20px;">';
                const labels = ['A', 'B', 'C', 'D'];
                
                for (let i = 0; i < 4; i++) {
                    const percent = data.poll_results[i] || 0;
                    pollHtml += `
                        <div style="display:flex; flex-direction:column; align-items:center; width:20%;">
                            <span style="font-size:0.85rem; font-weight:bold; margin-bottom:5px;">${percent}%</span>
                            <div style="width:100%; height:${percent * 1.2}px; background:linear-gradient(to top, var(--purple), var(--accent)); border-radius:4px;"></div>
                            <span style="font-weight:900; margin-top:8px; color:var(--yellow);">${labels[i]}</span>
                        </div>
                    `;
                }
                pollHtml += '</div>';

                // Gọi hàm hiển thị hộp thoại pop-up (Modal) kết quả khảo sát
                showModal('📊 Ý KIẾN KHÁN GIẢ TRONG ZÒNG TRÒN', pollHtml);
            } 
            else if (type === 'call') {
                // Trợ giúp gọi điện cho người thân: Hiển thị cuộc hội thoại giả lập của AI
                showModal('📞 ĐANG KẾT NỐI VỚI NGƯỜI THÂN...', `
                    <div style="padding:10px; line-height:1.6; font-size:1.05rem;">
                        <p style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">MC: "Alo, bạn có 30 giây để hỏi ý kiến người thân bắt đầu..."</p>
                        <blockquote style="background:rgba(255,255,255,0.05); padding:15px; border-left:4px solid var(--accent); border-radius:4px; font-style:italic;">
                            "${data.recommendation}"
                        </blockquote>
                    </div>
                `);
            }
        } else {
            alert('⚠️ Lỗi trợ giúp: ' + data.error);
        }
    } catch (err) {
        alert('❌ Không thể gọi quyền trợ giúp!');
    }
}
```

---

## 5. 💬 MC CHATBOT TRỢ LÝ ẢO (GEMINI AI CHAT)

Frontend quản lý hội thoại chat trực tiếp với MC Trợ lý ở góc phải màn hình:

```javascript
async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return; // Bỏ qua nếu tin nhắn trống

    // 1. Thêm tin nhắn của người chơi vào khung chat ngay lập tức
    addUserMessage(msg);
    input.value = ''; // Reset ô nhập liệu

    // Hiển thị bong bóng MC đang gõ chữ (...)
    showTypingIndicator();

    try {
        const res = await fetch(API_URL + '/api/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: msg })
        });
        const data = await res.json();
        
        removeTypingIndicator(); // Ẩn bong bóng chờ

        if (data.success) {
            // Thêm phản hồi của MC vào khung chat
            addBotMessage(data.reply);
        } else {
            addBotMessage("Xin lỗi, tôi đang mất kết nối máy chủ một chút!");
        }
    } catch (err) {
        removeTypingIndicator();
        addBotMessage("Không thể gửi tin nhắn!");
    }
}
```

---

## 6. 🔊 SYNTHESIZER ÂM THANH BẰNG CODE (WEB AUDIO API)

Hàm `playSound(type)` tự động tổng hợp sóng âm để phát nhạc mà không cần bất kỳ file nhạc `.mp3` nào:

```javascript
function playSound(type) {
    if (!soundEnabled) return; // Nếu người dùng tắt loa thì thoát ngay

    try {
        // 1. Khởi tạo đối tượng xử lý âm thanh tổng của trình duyệt
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioContext();

        // 2. Tạo bộ tạo sóng âm (Oscillator) và bộ điều khiển âm lượng (Gain)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        // Kết nối: Bộ sóng âm -> Bộ âm lượng -> Loa thiết bị
        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;

        // 3. Định nghĩa các tần số âm nhạc khác nhau cho từng kịch bản
        if (type === 'tick') {
            // Âm thanh đếm giây bíp bíp nhỏ kịch tính
            osc.frequency.setValueAtTime(880, now); // Tần số cao (880Hz)
            gain.gain.setValueAtTime(0.05, now);    // Âm lượng rất nhỏ (5%)
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
            osc.start(now);
            osc.stop(now + 0.1); // Kéo dài trong 0.1 giây
        } 
        else if (type === 'right') {
            // Âm chuông chiến thắng (2 nốt nhạc vang lên tăng dần)
            osc.type = 'triangle'; // Sóng tam giác êm dịu
            osc.frequency.setValueAtTime(523.25, now); // Nốt Đô (C5)
            osc.frequency.setValueAtTime(659.25, now + 0.15); // Nốt Mi (E5)
            
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        }
        else if (type === 'wrong') {
            // Âm còi báo sai (tần số tụt sâu đột ngột tạo cảm giác hụt hẫng)
            osc.type = 'sawtooth'; // Sóng răng cưa hơi rè giống tiếng còi
            osc.frequency.setValueAtTime(220, now); // Nốt La thấp (A3)
            osc.frequency.linearRampToValueAtTime(110, now + 0.5); // Tụt xuống 110Hz
            
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        }
        else if (type === 'select') {
            // Âm thanh hồi hộp khi chọn đáp án (Tiếng u u trầm)
            osc.type = 'sine'; // Sóng hình sin thuần khiết
            osc.frequency.setValueAtTime(150, now); // Tần số trầm (150Hz)
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 1.8);
            osc.start(now);
            osc.stop(now + 1.8);
        }
    } catch (e) {
        console.warn("Không hỗ trợ phát âm thanh:", e);
    }
}
```

---

## 7. 💬 CÁC HỘP THOẠI PROMPTS & MODALS TÙY BIẾN

Trò chơi không sử dụng lệnh `alert()` hay `prompt()` mặc định của trình duyệt vì chúng trông rất thô và làm ngắt quãng luồng xử lý của trang web. Thay vào đó, game sử dụng một lớp phủ (Modal Overlay) tùy biến viết bằng CSS và HTML.

```javascript
function showModal(title, body) {
    // 1. Gán nội dung tiêu đề và thân hộp thoại
    document.getElementById('modal-title').innerHTML = title;
    document.getElementById('modal-body').innerHTML = body;

    // 2. Thêm class 'active' vào overlay để hiển thị hộp thoại kèm hiệu ứng mượt mà
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    // Loại bỏ class 'active' để ẩn hộp thoại
    document.getElementById('modal-overlay').classList.remove('active');
}
```

---

## 🚀 ĐỀ XUẤT CÁC BÀI TẬP THỰC HÀNH TRÊN FILE `game.js`

1.  **Thay Đổi Tốc Độ Pháo Hoa Giấy (Confetti):**
    Tìm hàm `createConfetti()`. Bạn sẽ thấy đoạn code sinh các thẻ Div bay ngẫu nhiên. Thử tăng số lượng hạt pháo hoa sinh ra từ `50` hạt lên `150` hạt để tạo hiệu ứng chúc mừng hoành tráng hơn khi trả lời đúng!
2.  **Sáng Tác Âm Nhạc Trợ Giúp Mới:**
    Tìm đoạn xử lý `type === 'assist'` hoặc tự viết thêm một loại âm thanh mới (ví dụ chuỗi 3 nốt nhạc thăng hoa) bằng cách thêm điều kiện so sánh trong hàm `playSound`.
3.  **Tùy Biến Lời Chúc Mừng:**
    Tìm hàm `getCorrectMsg()`. Sửa đổi các câu thoại chúc mừng tiếng Việt hài hước trong mảng để tạo cá tính riêng cho MC Trợ lý ảo của bạn.
