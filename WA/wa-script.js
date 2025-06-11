//NOTE: jwt token expires, remember to replace with a new one.
const jwtToken = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNzQ1NDQwODE3LCJleHAiOjE3NDU0NDgwMTd9.XNw0jWJWpirv5-PBhoJnYrNtU7sdR6fp2-amV8sc2p5-zQpAZdmITFcYBpiZkLMYuFGW5_oIY4cVTFvmLxHGCJmonssNS1PwEFMAzn4yCjbb2TWwcTk2m9OqXezzUTiWp0V09BTxN3b6D1BQUj6N-RsIUWkOzefeeDQjag2WyAcijOyaU8dyqyIJ4KZspPDlU4qGVY552IQzPrFtNxZlDEAl1PQlRb3tac65SBEIyCPmv0BWh6GmOJK7eNAbGB5mC4bI7IFPmHu2W_LeKspUvCbDcXayveF-ou8rjj0-6_xD4QUgoqPo7mADqanLVAJsFoRp3I2rRNYmmMKM1iQpQg";
var g_wa_instance;
window.addEventListener("beforeunload", function () {
    sessionStorage.clear();
});

window.watsonAssistantChatOptions = {
    integrationID: "2c16d087-713f-409a-b9aa-6c674f0f26d6", //draft
    //integrationID: "5badefc1-489e-4d45-a675-c337e40923a1", //published
    region: "us-south",
    serviceInstanceID: "c7d52e6c-bc85-4fa2-a1c7-bb31765e1cb4",
    identityToken: jwtToken,
    onLoad: function (instance) {
        g_wa_instance = instance;

        instance.on({
            type: "customResponse",
            handler: (event, instance) => {
                if (
                    event.data.message.user_defined &&
                    event.data.message.user_defined.user_defined_type === "user-file-upload"
                ) {
                    fileUploadCustomResponseHandler(event, instance);
                }
            },
        });

        instance.render();
    }
};

function fileUploadCustomResponseHandler(event, instance) {
    const { element } = event.data;

    element.innerHTML = `
        <div>
            <input type="file" id="uploadInput" style="display: none;">
            <button id="uploadButton" class="WAC__button--primary WAC__button--primaryMd"> Upload a File </button>
        </div>`;

    const uploadInput = element.querySelector("#uploadInput");
    const button = element.querySelector("#uploadButton");

    button.addEventListener("click", () => uploadInput.click());

    uploadInput.addEventListener("change", (event) => {
        const selectedFile = event.target.files[0];
        if (selectedFile) {
            uploadFileFromAsst(selectedFile);
        }
    });
}

function uploadFileFromAsst(selectedFile) {
    if (!selectedFile) {
        console.error("No file selected.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    const UPLOAD_URL = "https://aimapper.1sqx96n7sll9.us-south.codeengine.appdomain.cloud/spec/upload";

    fetch(UPLOAD_URL, {
        method: "POST",
        headers: {
            'Authorization': 'Bearer '+jwtToken
        },
        body: formData
    })
    .then(async (response) => {
        const responseText = await response.text();
        console.log("Raw Response:", responseText);

        try {
            const data = JSON.parse(responseText);
            if (data && data["document_id"]) {
                const docId = data["document_id"];
                const msg = `File uploaded successfully. Document ID: ${docId}`;
                console.log(msg);
                messageChatbot(msg, docId ,false);
            } else {
                console.error("Unexpected API response format:", data);
                messageChatbot("File upload error. No document ID returned.", true);
            }
        } catch (parseError) {
            console.error("JSON Parse Error:", parseError);
            messageChatbot("File upload failed due to response error.", true);
        }
    })
    .catch((error) => {
        console.log(error);
        console.error("Error while uploading file to Watson Discovery:", error);
        messageChatbot("File upload failed due to an error.", true);
    });
}

function messageChatbot(txt, docid="", silent = false) {
    //console.log("Sending message to chatbot:", txt); 
    const context={
    skills: {
      ['actions skill']: {
        skill_variables: {
          document_id: docid,
        }
      }
    }
  }
    g_wa_instance.send({ input: { message_type: "text", text: txt },"context": context }, { silent })
        .catch(() => console.error("Sending message to chatbot failed"));
}

document.head.appendChild(Object.assign(document.createElement("script"), {
    src: "https://web-chat.global.assistant.watson.cloud.ibm.com/loadWatsonAssistantChat.js"
}));
