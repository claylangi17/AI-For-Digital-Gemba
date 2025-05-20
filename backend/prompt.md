Saya dan team developer saya ingin membuat sebuah website dan juga mobile app untuk project gemba digital with AI. disini saya dapat bagian membuat AInya, jadi outputnya kepada mereka dalam bentuk API yang nanti mereka akan gunakan untuk membuat website dan mobile app. Tech stack yang akan saya gunakan adalah Python, Langchain, Fast APi, dan MySQL. disini saya akan membuat 4 AI yang akan dibuat:
1. AI Root cause suggestion
- disini ainya itu bakal kasih beberapa possible root cause bersarkan kepintarannya dan juga berdasarkan data yang ada di database yang sudah dipelajarinya, disini saya mau tiap data baru yang akan ke submit ke database akan diolah oleh AI ini untuk membuat beberapa possible root cause lebih akurat lagi. disini ai bakal dapat informasi dari user:
    - machine/line
    - problem
setelah dapat informasi dari user, disini ai akan mencari di database saya dan filter berdasarkan machine/line yang di input oleh user. lalu dia akan pelajari semua problem dan root cause yang ada di database tersebut. setelah itu, dia akan membuat beberapa possible root cause berdasarkan data yang ada di database tersebut. 
2. AI Merge jawaban
- Disini ai akan merge beberapa root cause yang di input oleh user, jika mirip maka akan di merge menjadi satu root cause. disini user bakal input root cause, serta photonya. saya mau outputnya adalah root cause yang sudah di merge, photonya tetap sama. dan semua user yang input root cause tersebut.
3. AI Generate Corrective action & Preventive action
- disini ainya akan generate corrective action dan preventive action berdasarkan root cause yang di input oleh user tadi. disini saya mau ainya membaca database kita agar bisa lebih relevan dengan data data kita sudah pernah input.
4. AI Scoring root cause
- disini ketika user input root cause, maka root causenya akan diolah oleh AI mengikuti bench mark berikut. jadi setiap user yang input root cause akan ada nilainya  masing masing.