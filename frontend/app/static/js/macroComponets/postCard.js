import {
  initializeTemplate,
  apiTogglePostLike,
  apiTogglePostBookmark,
  apiGetPostMedia,
  apiUserPostsFeed,
  apiToggleRepostPosts,
  flash,
} from "../utils/base.js";
import { formatDate } from "../utils/datetime.js";
import { replyCard } from "./replyCard.js";

export async function postCard(
  clone,
  post,
  { type = "feed", mainCardClbk, parentCardClbk, addReplieClbk },
) {
  // If type = feed it means card is used for home feed and type = post so customize it for post screen
  if (!(type === "feed" || type === "post"))
    throw Error(`Invalid type used ${type}`);
  if (type === "feed") {
    clone.querySelector(".card").addEventListener("click", (e) => {
      if (
        e.target.closest(
          "a, button, .likeBtn, .bookmarkBtn, .shareBtn, .downloadBtn, .addReplie, #repostMenuContainer, #replieForm",
        )
      )
        return;

      // Go to post page
      mainCardClbk(post.postID);
    });
    // Add replie box
    const replieBtn = clone.querySelector(".addReplie");
    replieBtn.classList.remove("hidden");
    replieBtn.addEventListener("click", async (e) => {
      const parentCard = e.target.parentNode.parentNode;
      if (parentCard.querySelector("form")) {
        // Remove repliebox if already exists
        parentCard.querySelector("form").remove();
      } else {
        parentCard.appendChild(
          await replyCard(post.postID, post.replyingTo ?? [], post.userName),
        );
      }
    });
  } else {
    // Post page specific actions
  }
  clone.querySelector(".qoute").addEventListener("click", (e) => {
    this.navigator("/post/create?reqouteTo=" + post.postID);
  });
  clone.querySelector(".cardTitle").textContent = post.title;
  clone.querySelector(".cardInfo").textContent = post.tags;
  clone.querySelector(".postUserName").textContent = post.userName;
  clone.querySelector(".postUserPic").src = post.postUserPicUrl;

  if (post.fileType) {
    clone.querySelector(".media").classList.remove("hidden");
    if (post.fileType === "image") {
      clone.querySelector(".postContentImgPreview").src = post.postMediaUrl;
    } else if (post.fileType === "video") {
      clone.querySelector(".postContentImgPreview").classList.add("hidden");
      clone.querySelector(".postContentVidPreview").classList.remove("hidden");
      clone.querySelector(".postContentVidPreview").src = post.postMediaUrl;
    }
  }
  // Post replies count
  if (post.replieCount !== 0) {
    clone.querySelector(".replieCount").innerText =
      post.replieCount + " replies";
  }

  // Post like
  const likeBtn = clone.querySelector(".likeBtn");
  if (post.likeCount !== 0) {
    likeBtn.querySelector(".count").innerText = post.likeCount;
  }
  if (post.isLiked) {
    clone.querySelector("[data-unliked]").classList.add("hidden");
    clone.querySelector("[data-liked]").classList.remove("hidden");
  }
  likeBtn.querySelector(".svgs").addEventListener("click", async (event) => {
    try {
      let conn = await fetch(`${apiTogglePostLike}/${post.postID}`, {
        method: "PUT",
        credentials: "include",
      });
      let res = await conn.json();
      if (conn.ok) {
        const e = event.target.parentNode.parentNode;
        const liked = e.querySelector("[data-liked]");
        const unliked = e.querySelector("[data-unliked]");
        if (res.isLiked) {
          liked.classList.remove("hidden");
          unliked.classList.add("hidden");
          likeBtn.querySelector(".count").innerText = post.isLiked
            ? post.likeCount
            : post.likeCount + 1;
        } else {
          liked.classList.add("hidden");
          unliked.classList.remove("hidden");
          likeBtn.querySelector(".count").innerText = post.isLiked
            ? post.likeCount - 1
            : post.likeCount;
        }
      }
      console.log(res);
    } catch (e) {
      console.error(e);
    }
  });

  // Post repost
  const repostBtn = clone.querySelector(".repostBtn");
  const repostRealBtn = clone.querySelector(".repost");

  if (post.repostCount !== 0) {
    repostBtn.querySelector(".count").innerText = post.repostCount;
    repostRealBtn.innerText = "Remove repost";
  }
  if (post.isReposted) {
    clone.querySelector("[data-unreposted]").classList.add("hidden");
    clone.querySelector("[data-reposted]").classList.remove("hidden");
  }
  repostRealBtn.addEventListener("click", async (event) => {
    try {
      let conn = await fetch(`${apiToggleRepostPosts}/${post.postID}`, {
        method: "PUT",
        credentials: "include",
      });
      let res = await conn.json();
      if (conn.ok) {
        const reposted = repostBtn.querySelector("[data-reposted]");
        const unreposted = repostBtn.querySelector("[data-unreposted]");
        if (res.isReposted) {
          reposted.classList.remove("hidden");
          unreposted.classList.add("hidden");
          repostBtn.querySelector(".count").innerText = post.isReposted
            ? post.repostCount
            : post.repostCount + 1;
          repostRealBtn.innerText = "Undo repost";
        } else {
          reposted.classList.add("hidden");
          unreposted.classList.remove("hidden");
          repostBtn.querySelector(".count").innerText = post.isReposted
            ? post.repostCount - 1
            : post.repostCount;
          repostRealBtn.innerText = "Repost";
        }
      }
      console.log(res);
    } catch (e) {
      console.error(e);
    }
  });
  // Post Bookmark
  const bookmarkBtn = clone.querySelector(".bookmarkBtn");
  if (post.bookmarkCount !== 0) {
    bookmarkBtn.querySelector(".count").innerText = post.bookmarkCount;
  }

  if (post.isBookmarked) {
    clone.querySelector("[data-unbookmarked]").classList.add("hidden");
    clone.querySelector("[data-bookmarked]").classList.remove("hidden");
  }
  bookmarkBtn
    .querySelector(".svgs")
    .addEventListener("click", async (event) => {
      try {
        let conn = await fetch(`${apiTogglePostBookmark}/${post.postID}`, {
          method: "PUT",
          credentials: "include",
        });
        let res = await conn.json();
        if (conn.ok) {
          const e = event.target.parentNode.parentNode;
          const bookmarked = e.querySelector("[data-bookmarked]");
          const unbookmarked = e.querySelector("[data-unbookmarked]");
          if (res.isBookmarked) {
            bookmarked.classList.remove("hidden");
            unbookmarked.classList.add("hidden");
            bookmarkBtn.querySelector(".count").innerText = post.isBookmarked
              ? post.bookmarkCount
              : post.bookmarkCount + 1;
          } else {
            bookmarked.classList.add("hidden");
            unbookmarked.classList.remove("hidden");
            bookmarkBtn.querySelector(".count").innerText = post.isBookmarked
              ? post.bookmarkCount - 1
              : post.bookmarkCount;
          }
        }
      } catch (e) {
        console.error(e);
      }
    });
  // Share Button
  const shareBtn = clone.querySelector(".shareBtn");
  shareBtn.querySelector(".svgs").addEventListener("click", async (e) => {
    const uncopied = shareBtn.querySelector("[data-uncopied]");
    const copied = shareBtn.querySelector("[data-copied]");
    const shareText = shareBtn.querySelector(".shareText");

    try {
      uncopied.classList.add("hidden");
      copied.classList.remove("hidden");
      shareText.innerText = "Copied!";
      shareText.classList.add("text-purple-500");
      await navigator.clipboard.writeText(
        `${window.location.origin}/i/${post.postID}`,
      );
      flash("Copied to clipboard!", "success");
      setTimeout(() => {
        uncopied.classList.remove("hidden");
        copied.classList.add("hidden");
        shareText.innerText = "Share";
        shareText.classList.remove("text-purple-500");
      }, 3000);
    } catch (error) {
      console.error(error.message);
    }
  });
  // Download Button
  const downloadBtn = clone.querySelector(".downloadBtn");
  downloadBtn.addEventListener("click", (e) => {
    window.location.href = `${apiGetPostMedia}/${post.postID}`;
    // Good for showing ads
    // window.open(
    //   `${apiGetPostMedia}/${post.postID}`,
    //   "_blank",
    // );
  });
  // Link of creator's profile
  clone.querySelector(".postUserPic").src = post.profileImgUrl;
  clone.querySelector(".postUserName").href = `/${post.userName}`;
  clone.querySelector(".userProfileLink").href = `/${post.userName}`;
  clone.querySelector(".createdAt").innerText = formatDate(post.createdAt);

  // Load parent post
  if (post.parentPostID?.payload) {
    const parentPost = post.parentPostID.payload;
    let parentPostContainer = clone.querySelector(".parentPostContainer");
    if (parentPostContainer) {
      parentPostContainer.classList.remove("hidden");
      const parentMacro = await initializeTemplate({
        macro: "parent",
      });
      const cloneParentMacro = parentMacro.content.cloneNode(true);
      cloneParentMacro.querySelector(".card").addEventListener("click", (e) => {
        if (e.target.closest(".card")) {
          // Send clbk
          parentCardClbk(parentPost.postID);
        }
      });
      if (parentPost.fileType) {
        cloneParentMacro.querySelector(".media").classList.remove("hidden");
        if (parentPost.fileType === "image") {
          cloneParentMacro.querySelector(".postContentImgPreview").src =
            parentPost.postMediaUrl;
        } else if (parentPost.fileType === "video") {
          cloneParentMacro
            .querySelector(".postContentImgPreview")
            .classList.add("hidden");
          cloneParentMacro
            .querySelector(".postContentVidPreview")
            .classList.remove("hidden");
          cloneParentMacro.querySelector(".postContentVidPreview").src =
            parentPost.postMediaUrl;
        }
      }
      cloneParentMacro.querySelector(".cardTitle").textContent =
        parentPost.title;
      cloneParentMacro.querySelector(".postUserName").textContent =
        parentPost.userName;
      cloneParentMacro.querySelector(".userProfileLink").href =
        `/user/${parentPost.userName}`;
      cloneParentMacro.querySelector(".postUserPic").src =
        parentPost.profileImgUrl;
      cloneParentMacro.querySelector(".createdAt").innerText = formatDate(
        parentPost.createdAt,
      );

      parentPostContainer.appendChild(cloneParentMacro);
    }
  }
  return clone;
}
