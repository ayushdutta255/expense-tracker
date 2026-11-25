// Small interactions for PennyWise (pop-up forms and delete confirmation)

const addDialog = document.getElementById("addDialog");
const budgetDialog = document.getElementById("budgetDialog");
const txForm = document.getElementById("txForm");
const addAction = txForm.action; // where the "Add" form posts to

// Close a pop-up with its X button or by tapping outside it
[addDialog, budgetDialog].forEach(function (dialog) {
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) dialog.close();
  });
  dialog.querySelectorAll("[data-close]").forEach(function (button) {
    button.onclick = function () { dialog.close(); };
  });
});

// Show the categories that match Expense / Income
function showCategories() {
  const kind = document.querySelector("input[name=kind]:checked").value;
  document.querySelectorAll(".chips[data-kind]").forEach(function (group) {
    const visible = group.dataset.kind === kind;
    group.hidden = !visible;
    group.querySelectorAll("input").forEach(function (input) { input.disabled = !visible; });
    // make sure one category is always selected in the visible group
    if (visible && !group.querySelector("input:checked")) {
      group.querySelector("input").checked = true;
    }
  });
}
document.querySelectorAll("input[name=kind]").forEach(function (radio) {
  radio.onchange = showCategories;
});

// "+ Add" opens an empty form
document.getElementById("openAdd").onclick = function () {
  txForm.reset();
  txForm.action = addAction;
  document.getElementById("txTitle").textContent = "New transaction";
  showCategories();
  addDialog.showModal();
};

// The pencil button opens the same form, already filled in
document.querySelectorAll(".edit").forEach(function (button) {
  button.onclick = function () {
    const data = button.dataset;
    txForm.reset();
    txForm.action = addAction.replace(/\/add$/, "/edit/" + data.id);
    txForm.querySelector("input[name=kind][value=" + data.kind + "]").checked = true;
    showCategories();
    const category = txForm.querySelector('.chips[data-kind=' + data.kind + '] input[value="' + data.category + '"]');
    if (category) category.checked = true;
    txForm.elements["amount"].value = data.amount;
    txForm.elements["description"].value = data.description;
    txForm.elements["date"].value = data.date;
    document.getElementById("txTitle").textContent = "Edit transaction";
    addDialog.showModal();
  };
});

document.getElementById("openBudget").onclick = function () { budgetDialog.showModal(); };

// Ask before deleting
document.querySelectorAll(".delete-form").forEach(function (form) {
  form.onsubmit = function () { return confirm("Delete this transaction?"); };
});
