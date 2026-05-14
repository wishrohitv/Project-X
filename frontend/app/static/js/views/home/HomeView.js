import AbstractView from "../AbstractView.js";
import { initializeTemplate, apiHomeFeed } from "../../utils/base.js";
import { postCard } from "../../macroComponets/postCard.js";
import { ScrollManager } from "../../utils/scrollManager.js";

export default class extends AbstractView {
  constructor(params) {
    super(params);
    this.title = "MemeStore";
    this.setTitle(this.title);

    // Remember the length of post object and offset
    this.postObjLength = 0; // Initial length is 0 but after first fetch it will be updated
    this.offset = 0;
    this.limit = 10;
    this.tabName = "all";
    // Network request status for debouncing
    this.isLoading = false;

    ScrollManager.add("home", () => {
      this.handleScroll();
    });
  }

  async getHtml(navigator) {
    this.navigator = navigator;
    try {
      const html = await fetch(
        "./static/js/views/home/templates/daisyUI/home.html",
      );

      const page = await html.text();
      this.page = document.createElement("div");
      this.page.innerHTML = page;
      // Container of post preview
      this.postContainer = this.page.querySelector("#postContainer");
      // Tab change listener
      const homeTabs = this.page.querySelectorAll("[name='home_tab']");
      homeTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          this.handleTabChange(tab);
        });
      });
      // Spinner
      this.spinner = this.page.querySelector("#spinner");

      // Fetch home feed
      this.loadHomeFeed();
    } catch (error) {
      console.error("Error fetching HTML:", error);
      this.page = "<h1>Error</h1><p>Failed to load page</p>";
    }
    return this.page;
  }

  // Function to fetch home feed for user
  async fetcFeed(url) {
    this.isLoading = true;

    let connection = await fetch(url, {
      method: "GET",
      credentials: "include",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
      },
    });
    let res = await connection.json();
    try {
      if (connection.ok) {
        this.postObjLength = res.payload.length;
        this.isLoading = false;
        return res.payload;
      } else {
        this.isLoading = false;
        return null;
      }
    } catch (error) {
      console.error(error);
      this.isLoading = false;
      throw new Error(error);
    }
  }

  async loadHomeFeed() {
    let url = `${apiHomeFeed}?limit=${this.limit}&offset=${this.offset}`;
    if (this.tabName === "template") {
      url = `${apiHomeFeed}?limit=${this.limit}&offset=${this.offset}&template=true`;
    } else {
      // TODO : implement all category feed
      url = `${apiHomeFeed}?limit=${this.limit}&offset=${this.offset}`;
    }

    this.spinner.classList.remove("hidden");
    initializeTemplate({}).then(async (postTemplate) => {
      /// Fetch home feed data
      const feedData = await this.fetcFeed(url);
      // Check if feedData is not empty
      if (feedData) {
        // postTemplate comming from base.js
        // Loop feedData list
        feedData.forEach(async (post) => {
          const clone = postTemplate.content.cloneNode(true);
          let card = await postCard(clone, post, {
            mainCardClbk: (postID) => {
              this.navigator("/i/" + postID);
            },
            parentCardClbk: (parentPostID) => {
              this.navigator("/i/" + parentPostID);
            },
          });
          this.postContainer.appendChild(card);
        });
      } else {
        console.error(feedData);
      }
      this.spinner.classList.add("hidden");
    });
  }

  async handleScroll(event) {
    if (
      window.scrollY + window.innerHeight >=
      document.documentElement.scrollHeight - 1
    ) {
      console.log("Debouncing... checking");
      if (this.isLoading) return;
      if (this.postObjLength < this.limit) return;
      console.log("Debouncing...");
      this.offset += this.limit;
      await this.loadHomeFeed();
    }
  }

  async handleTabChange(tab) {
    // Reset post container and offset if tab changes
    if (tab.id !== this.tabName) {
      this.tabName = tab.id;
      this.postContainer.innerHTML = "";
      this.offset = 0;
      await this.loadHomeFeed();
    }
  }
}
