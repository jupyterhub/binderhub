import { BASE_URL } from "./constants";

let configDict = {};

function setLabels() {
  const provider = $("#provider_prefix").val();
  const text = configDict[provider]["text"];
  const tag_text = configDict[provider]["tag_text"];
  const ref_prop_disabled = configDict[provider]["ref_prop_disabled"];
  const label_prop_disabled = configDict[provider]["label_prop_disabled"];
  const placeholder = "HEAD";

  $("#ref").attr('placeholder', placeholder).prop("disabled", ref_prop_disabled);
  $("label[for=ref]").text(tag_text).prop("disabled", label_prop_disabled);
  $("#repository").attr('placeholder', text);
  $("label[for=repository]").text(text);
}

export function updateRepoText() {
  if (Object.keys(configDict).length === 0) {
    const configUrl = BASE_URL + "_config";
    fetch(configUrl).then(resp => {
      resp.json().then(data => {
        configDict = data
        setLabels();
      });
    })
  } else {
    setLabels();
  }
}
