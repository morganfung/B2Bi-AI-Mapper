<%@ page import="java.util.*, java.security.*, java.util.Base64, java.nio.file.*, java.security.spec.PKCS8EncodedKeySpec" %>
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%
    // JWT Header and Payload
    String headerJson = "{\"alg\":\"RS256\",\"typ\":\"JWT\"}";

    long currentTime = System.currentTimeMillis() / 1000;
    long expirationTime = currentTime + 86400;

    String payloadJson = "{"
            + "\"sub\":\"1234567890\","
            + "\"name\":\"John Doe\","
            + "\"iat\":" + currentTime + ","
            + "\"exp\":" + expirationTime
            + "}";

    // Base64URL encode
    Base64.Encoder urlEncoder = Base64.getUrlEncoder().withoutPadding();
    String encodedHeader = urlEncoder.encodeToString(headerJson.getBytes("UTF-8"));
    String encodedPayload = urlEncoder.encodeToString(payloadJson.getBytes("UTF-8"));
    String message = encodedHeader + "." + encodedPayload;

    // Load Private Key from PEM File
    String pemPath = application.getRealPath("/WEB-INF/key.pem"); 
    String privateKeyPem = new String(Files.readAllBytes(Paths.get(pemPath)), "UTF-8");

    privateKeyPem = privateKeyPem
        .replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", "")
        .replaceAll("\\s", ""); // Remove newlines and spaces

    byte[] keyBytes = Base64.getDecoder().decode(privateKeyPem);
    PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(keyBytes);
    KeyFactory keyFactory = KeyFactory.getInstance("RSA");
    PrivateKey privateKey = keyFactory.generatePrivate(keySpec);

    // Sign JWT
    Signature signature = Signature.getInstance("SHA256withRSA");
    signature.initSign(privateKey);
    signature.update(message.getBytes("UTF-8"));
    byte[] signatureBytes = signature.sign();
    String encodedSignature = urlEncoder.encodeToString(signatureBytes);

    String jwt = message + "." + encodedSignature;

%>

<script>
    const jwtToken = "<%= jwt %>";
    var g_wa_instance;
window.addEventListener("beforeunload", function () {
    sessionStorage.clear();
});

window.watsonAssistantChatOptions = {
    //integrationID: "2c16d087-713f-409a-b9aa-6c674f0f26d6", //draft
    integrationID: "5badefc1-489e-4d45-a675-c337e40923a1", //published
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
        const data = JSON.parse(responseText);
        const msg = "File uploaded successfully. Document ID: " + data["document_id"];
        messageChatbot(msg, data["document_id"] ,false);
    })
    .catch((error) => {
        console.error("Error while uploading file to Watson Discovery:", error);
        messageChatbot("File upload failed due to an error.", true);
    });
}

function messageChatbot(txt, docid="", silent = false) {
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

</script>

