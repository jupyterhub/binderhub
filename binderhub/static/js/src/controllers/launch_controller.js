import { Controller } from "stimulus"

export default class extends Controller {
  static targets = [ "url" ]

  launch() {
    const element = this.urlTarget
    const url = element.value
    console.log("Hello! Launching:", url)
  }
}
