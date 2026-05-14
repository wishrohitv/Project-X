// Api endpoint
const baseUrl = "http://127.0.0.1:5000";
export const apiLoginUser = `${baseUrl}/api/v1/auth/login`;
export const apiSignupUser = `${baseUrl}/api/v1/auth/signup`;
export const apiLogoutUser = `${baseUrl}/api/v1/auth/logout`;
export const apiUploadPosts = `${baseUrl}/api/v1/posts/upload`;
export const apiToggleRepostPosts = `${baseUrl}/api/v1/posts/repost`;
export const apiUserInSession = `${baseUrl}/api/v1/user/auth`;
export const apiUser = `${baseUrl}/api/v1/user`;
export const apiProfileImage = `${baseUrl}/api/v1/getProfileImage`;
export const apiUserUpdateProfile = `${baseUrl}/api/v1/user/update`;
export const apiUserUpdateProfileImg = `${baseUrl}/api/v1/user/profileImg/update`;
export const apiUserPostsFeed = `${baseUrl}/api/v1/posts`;
export const apiHomeFeed = `${baseUrl}/api/v1/feed`;
export const apiAddFollower = `${baseUrl}/api/v1/user/follow`;
export const apiRemoveFollower = `${baseUrl}/api/v1/user/unfollow`;
export const apiTogglePostLike = `${baseUrl}/api/v1/posts/like`;
export const apiTogglePostBookmark = `${baseUrl}/api/v1/posts/bookmark`;
export const apiRefreshToken = `${baseUrl}/api/v1/auth/refresh`;
export const apiGetPostMedia = `${baseUrl}/api/v1/getPostMedia`;

export const apiPostsReplies = `${baseUrl}/api/v1/posts/replies`;

// Global user object
export function setUser(sessionUser) {
  localStorage.setItem("payload", JSON.stringify(sessionUser));
}

export function getUser() {
  let _user = localStorage.getItem("payload");
  return _user ? JSON.parse(_user) : null;
}

export function deleteUser() {
  localStorage.removeItem("payload");
}

// Store macro components in memory
let postMacroTemplate = {};

export async function initializeTemplate({ macro = "feed" }) {
  let templateHtml;
  let templateID;
  const feedPostMacro =
    "/static/daisyUI/macroComponent/feedPostLayoutMacro.html";
  const userPostMacro =
    "/static/daisyUI/macroComponent/userPostLayoutMacro.html";
  const userPostMacroParent =
    "/static/daisyUI/macroComponent/feedPostLayoutParentMacro.html";

  let loadMacro; // Default is feedPostMacro
  switch (macro) {
    case "feed":
      loadMacro = feedPostMacro;
      templateID = "feedPostCardMacro";
      break;
    case "user":
      loadMacro = userPostMacro;
      templateID = "userPostCardMacro";
      break;
    case "parent":
      loadMacro = userPostMacroParent;
      templateID = "postCardMacroParent";
      break;
    default:
      loadMacro = feedPostMacro;
  }
  try {
    if (postMacroTemplate[loadMacro]) {
      templateHtml = postMacroTemplate[loadMacro];
    } else {
      const res = await fetch(loadMacro);
      templateHtml = await res.text();

      // Add template to memory
      postMacroTemplate[loadMacro] = templateHtml;

      // Create a temporary container element
      const tempContainer = document.createElement("div");
      tempContainer.innerHTML = templateHtml;

      document.body.appendChild(tempContainer);
    }

    const postTemplate = document.getElementById(templateID);
    return postTemplate; // resolve when fully loaded
  } catch (error) {
    console.error(error);
  }
}

export async function fetchUserInfo() {
  // Check if user is logged in
  if (!getUser()) return;
  try {
    const res = await fetch(apiUserInSession, {
      method: "GET",
      credentials: "include",
    });
    const resObj = await res.json();
    if (res.ok) {
      setUser(resObj.payload);
      manageNavbar();
    } else if (res.status === 401) {
      await refreshToken();
    }
  } catch (error) {
    console.error(error);
  }
}

export async function refreshToken() {
  try {
    const response = await fetch(apiRefreshToken, {
      headers: {
        "Content-Type": "application/json",
      },
      method: "GET",
      credentials: "include",
    });

    const data = await response.json();
    if (response.ok) {
      console.log(data);
      await fetchUserInfo();
    } else {
      flash("Session expired. Please log in again.", { messageType: "error" });
      // Clear user data
      deleteUser();
      // Update navbar
      manageNavbar();
      console.error(data);
    }
  } catch (error) {
    console.error(error);
  }
}

// Navbar
export function manageNavbar() {
  const profileBtnContainer = document.getElementById("profileBtnContainer");
  const signupLoginContainer = document.getElementById("signupLoginContainer");
  const user = getUser();
  if (user) {
    profileBtnContainer.classList.remove("hidden");
    const ankerTag = profileBtnContainer.querySelector("#goToProfile");
    ankerTag.href = `/${user.username}`;
    const loggedProfileLogo =
      profileBtnContainer.querySelector("#loggedProfileLogo");
    loggedProfileLogo.src = user.profileImgUrl;
    signupLoginContainer.classList.add("hidden");
  }
}

export function flash(message, { duration = 3000, messageType = "success" }) {
  let bgColor;
  switch (messageType) {
    case "success":
      bgColor = "#4caf50";
      break;
    case "error":
      bgColor = "#f44336";
      break;
    case "warning":
      bgColor = "#ffc107";
      break;
    case "info":
      bgColor = "#2196f3";
      break;
    default:
      bgColor = "#212121";
  }

  const toast = document.querySelector(".toast");
  toast.textContent = message;
  toast.style.backgroundColor = bgColor;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}
