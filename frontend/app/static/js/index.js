import HomeView from "./views/home/HomeView.js";
import GuidelinesView from "./views/guidelines/GuidelinesView.js";
import AboutView from "./views/about/AboutView.js";
import TermconditionView from "./views/termConditions/TermconditionView.js";
import PrivacypolicyView from "./views/privacyPolicy/PrivacypolicyView.js";
import LoginView from "./views/login/LoginView.js";
import LogoutView from "./views/logout/LogoutView.js";
import SignupView from "./views/signup/SignupView.js";
import ProfileView from "./views/profile/ProfileView.js";
import PostView from "./views/posts/PostView.js";
import EditProfileView from "./views/profile/EditProfileView.js";
import CreatePostView from "./views/posts/CreatePostView.js";
import { fetchUserInfo, manageNavbar } from "./utils/base.js";
import { ScrollManager } from "./utils/scrollManager.js";

const pathToRegex = (path) =>
  new RegExp("^" + path.replace(/\//g, "\\/").replace(/:\w+/g, "(.+)") + "$");

const getParams = (match) => {
  const values = match.result.slice(1);
  const keys = Array.from(match.route.path.matchAll(/:(\w+)/g)).map(
    (result) => result[1],
  );

  return Object.fromEntries(
    keys.map((key, i) => {
      return [key, [values[i]]];
    }),
  );
};

const navigateTo = (url) => {
  history.pushState(null, null, url);
  router();
};

const router = async () => {
  // Clear scroll manager if exists
  ScrollManager.clear();
  const routes = [
    { path: "/", view: HomeView },
    { path: "/guidelines", view: GuidelinesView },
    { path: "/terms-conditions", view: TermconditionView },
    { path: "/privacy-policy", view: PrivacypolicyView },
    { path: "/more/about", view: AboutView },
    { path: "/auth/login", view: LoginView },
    { path: "/auth/logout", view: LogoutView },
    { path: "/auth/signup", view: SignupView },
    { path: "/edit/profile/:username", view: EditProfileView },
    { path: "/:username", view: ProfileView },
    { path: "/post/create", view: CreatePostView },
    { path: "/i/:postID", view: PostView },
  ];

  // Test each route for potential match
  const potentialMatches = routes.map((route) => {
    // Get pathname form URL parser and This way we can get params (hash) e.g. ?user=123
    const pathname = new URL(location.href).pathname;
    return {
      route: route,
      result: pathname.match(pathToRegex(route.path)),
    };
  });

  let match = potentialMatches.find(
    (potentialMatch) => potentialMatch.result !== null,
  );

  if (!match) {
    match = {
      route: routes[0],
      result: [location.pathname],
    };
  }

  const view = new match.route.view(getParams(match));

  document.querySelector("#app").replaceChildren(
    await view.getHtml((goTo) => {
      navigateTo(goTo);
    }),
  );
};

window.addEventListener("popstate", router);

document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("click", (e) => {
    const link = e.target.closest("[data-link]");
    if (link) {
      e.preventDefault();
      if (window.scrollY > 0) {
        window.scrollTo({
          top: 0,
          behavior: "instant",
        });
      }
      navigateTo(link.href);
    }
  });
  router();
});

fetchUserInfo();
manageNavbar();
