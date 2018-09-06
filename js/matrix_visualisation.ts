declare var $: any;

class MatrixData {
    matrix: boolean[][];
    columns: string[];
    rows: string[];

    constructor(matrix: boolean[][], rows: string[], columns: string[]) {
        this.matrix = matrix;
        this.columns = columns;
        this.rows = rows;
    }
}

class OverlayData {
    matrix: number[][];
    columns: string[];
    rows: string[];

    constructor(matrix: number[][], rows: string[], columns: string[]) {
        this.matrix = matrix;
        this.columns = columns;
        this.rows = rows;
    }
}

class GeneratedRole {
    users: number[];
    permissions: number[];
    render: boolean;

    constructor(users: number[], permissions: number[], render: boolean) {
        this.users = users;
        this.permissions = permissions;
        this.render = render;
    }
}

class MatrixRenderer {
    data: MatrixData;

    canvas_container: string;
    canvas_element: HTMLCanvasElement;
    canvas_context: CanvasRenderingContext2D;

    previous_cursor: number[] = null;

    is_panning: boolean = false;
    is_selecting: boolean = false;
    is_extending: boolean = false;
    is_extending_adding: boolean;

    meta_user: any[] = null;
    meta_user_totals: any[] = null;
    meta_permission: any[] = null;
    meta_permission_totals: any[] = null;

    pan_offset: number[];

    scaling_factor: number = 1;
    min_scaling_factor: number = 0;

    is_first_selection: boolean = true;
    selection_start: number[];
    selection: number[][];
    extended_selection: number[][];

    already_generated: GeneratedRole[] = [];
    overlay: OverlayData = null;
    overlay_range: number[];

    constructor(canvas_handle: string, data: MatrixData) {
        this.data = data;

        this.canvas_container = canvas_handle;

        let container_element = $(this.canvas_container);

        let container_width = container_element.width();
        let container_height = container_element.height();

        container_element.html("<canvas id='matrix_canvas' width='" + container_width + "' height='" + container_height + "'></canvas>");
        this.canvas_element = document.getElementById("matrix_canvas") as HTMLCanvasElement;
        this.canvas_context = this.canvas_element.getContext("2d");

        this.scaling_factor = Math.max(container_width / this.data.columns.length, container_height / this.data.rows.length);
        this.min_scaling_factor = this.scaling_factor;

        this.pan_offset = [0, 0];

        this.canvas_element.addEventListener('mouseup', (this.mouse_up).bind(this), false);
        this.canvas_element.addEventListener('mousedown', (this.mouse_down).bind(this), false);
        this.canvas_element.addEventListener('mousemove', (this.mouse_move).bind(this), false);
        this.canvas_element.addEventListener('wheel', (this.mouse_wheel).bind(this), false);
        document.addEventListener('keydown', (this.key_press).bind(this), false);
    }

    save_current_selection(): void {
        if (this.is_first_selection) {
            alert('Please make a selection first.');
            return;
        }

        let role_name = prompt("What name should this role have?");
        if (confirm("You are about to save a role - " + role_name + " - containing " + this.get_role_selection()[0].length + " users and " + this.get_role_selection()[1].length + " permissions. Continue?")) {
            $((function () {
                $.ajax({
                    url: "/submit_role",
                    method: 'post',
                    data: JSON.stringify({
                        'name': role_name,
                        'users': this.get_role_selection()[0],
                        'permissions': this.get_role_selection()[1]
                    }),
                    success: function () {
                        alert("This role has been saved!");
                        window.location.reload();
                    },
                    error: function () {
                        alert("Something went wrong. Please try again.")
                    }
                })
            }).bind(this, role_name));

        } else {
            alert('This role has NOT been saved.');
        }

    }

    explore_current_selection(): void {
        if (this.is_first_selection) {
            alert('Please make a selection first.');
            return;
        }

        let users = this.get_role_selection()[0].sort();
        let perms = this.get_role_selection()[1].sort();
        let superf = this.get_superfluous_assignments();

        $("#matrix_selection_users").html('');
        $.each(users, function (u, user) {
            $('#matrix_selection_users').append($('<option>', {text: user}));
        });

        $("#matrix_selection_perms").html('');
        $.each(perms, (function (p, perm) {
            if (perm in this.meta_permission) {
                let permission: any = this.meta_permission[perm];
                $("#matrix_selection_perms").append($('<option>', {text: permission.name + ", " + permission.description}));
            } else {
                $('#matrix_selection_perms').append($('<option>', {text: perm}));
            }
        }).bind(this));

        $("#matrix_selection_superf").html('');
        $.each(superf, (function (a, assignment) {
            $('#matrix_selection_superf').append($('<option>', {
                text: (this.meta_user != null ? this.meta_user[assignment[0]].user : assignment[0]) +
                ", " + (this.meta_permission != null ? this.meta_permission[assignment[1]].name : assignment[1])
            }));
        }).bind(this));

        if (this.meta_user != null) {
            $("#matrix_selection_user_meta_container").show();
            $("#matrix_selection_user_meta").html("");
            let selection_meta_user = calc_totals_over_group(users, this.meta_user);
            for (let p in selection_meta_user) {
                let prop = selection_meta_user[p];
                if (sparse_length(prop) > 0.8 * users.length) {
                    continue;
                }
                let listgroup = $("<ul/>").addClass("list-group").appendTo($("#matrix_selection_user_meta"));
                $("<li/>").addClass("list-group-item").addClass("active").text(p).appendTo(listgroup);
                for (let v in prop) {
                    let value = prop[v];
                    let perc: number = value / this.meta_user_totals[p][v] * 100;
                    $("<li/>").addClass("list-group-item").text(v + " (" + value + "/" +
                        this.meta_user_totals[p][v] + ", " + perc.toFixed(2) + "%)").appendTo(listgroup);
                }
            }
        }

        if (this.meta_permission != null) {
            $("#matrix_selection_perm_meta_container").show();
            $("#matrix_selection_perm_meta").html("");
            let selection_meta_perm = calc_totals_over_group(perms, this.meta_permission);
            for (let p in selection_meta_perm) {
                let prop = selection_meta_perm[p];
                if (sparse_length(prop) > 0.8 * perms.length) {
                    continue;
                }
                let listgroup = $("<ul/>").addClass("list-group").appendTo($("#matrix_selection_perm_meta"));
                $("<li/>").addClass("list-group-item").addClass("active").text(p).appendTo(listgroup);
                for (let v in prop) {
                    let value = prop[v];
                    let perc: number = value / this.meta_permission_totals[p][v] * 100;
                    $("<li/>").addClass("list-group-item").text(v + " (" + value + "/" +
                        this.meta_permission_totals[p][v] + ", " + perc.toFixed(2) + "%)").appendTo(listgroup);
                }
            }
        }

        $("#exploration_modal").modal();
    }

    propose_selection(threshold: number = 0): void {

        if (this.previous_cursor == null) {
            alert("Please hover over a cell first.");
            return;
        }
        if (!this.data.matrix[this.previous_cursor[1]][this.previous_cursor[0]]) {
            alert("Please select a cell with an authorisation.");
            return;
        }
        if (this.selection != null) {
            if (!confirm('You already have a selection. Discard this selection?')) {
                return;
            }
        }

        this.selection = [
            [this.previous_cursor[0], this.previous_cursor[1]],
            [this.previous_cursor[0], this.previous_cursor[1]]
        ];

        this.selection_start = null;
        this.extended_selection = [[], []];
        this.is_first_selection = false;

        let direction_updown = true;
        let fix_direction: number = null;
        let do_loop = true;

        while (do_loop == true) {

            let deltas: number[] = [-1, 1];
            let directions: number[] = [0, 1];

            let direction_stops = 0;

            for (let direction in directions) {

                if (fix_direction != null && +direction != fix_direction) {
                    continue;
                }

                let delta_stops = 0;

                for (let delta in deltas) {

                    let d: number = deltas[delta];
                    let corner: number = (d == -1 ? 0 : 1);
                    let corner_cell: number[] = this.selection[corner].slice();
                    let next_cell: number[] = corner_cell.slice();

                    next_cell[direction] += d;

                    if (
                        !(next_cell[1] in this.data.matrix) ||
                        !(next_cell[0] in this.data.matrix[next_cell[1]]) ||
                        !this.data.matrix[next_cell[1]][next_cell[0]]
                    ) {
                        delta_stops += 1;
                    } else {
                        this.selection[corner] = next_cell;
                    }

                    if (delta_stops > 1) {
                        if (fix_direction == null) {
                            fix_direction = (1 - +direction);
                        } else {
                            do_loop = false;
                            break;
                        }
                    }

                }

            }

        }

        this.render();

    }

    revoke_current_selection(): void {
        this.apply_current_selection(false);
    }

    grant_current_selection(): void {
        this.apply_current_selection(true);
    }

    apply_current_selection(grant: boolean) {
        if (this.is_first_selection) {
            alert('Please make a selection first.');
            return;
        } else {
            let word: string = grant ? 'grant' : 'revoke';
            if (confirm("You are about to " + word + " " + this.get_role_selection()[1].length + " permissions on " + this.get_role_selection()[0].length + " users in the ORIGINAL assignment. This cannot be easily reversed and is only meant to correct mistakes in the original assignment. Continue?")) {
                $((function () {
                    $.ajax({
                        url: "/apply_selection",
                        method: 'post',
                        data: JSON.stringify({
                            'users': this.get_role_selection()[0],
                            'permissions': this.get_role_selection()[1],
                            'grant': grant
                        }),
                        success: function () {
                            alert("Changes saved!");
                            window.location.reload();
                        },
                        error: function () {
                            alert("Something went wrong. Please try again.")
                        }
                    })
                }).bind(this, grant));

            } else {
                alert('Changes where NOT saved.');
            }
        }

    }

    get_role_selection(names: boolean = true): any[][] {
        if (this.is_first_selection) {
            return [[], []];
        }
        let extended_users: number[] = this.extended_selection[1];
        let extended_permissions: number[] = this.extended_selection[0];
        let users: number[] = range(this.selection[0][1], this.selection[1][1]);
        let permissions: number[] = range(this.selection[0][0], this.selection[1][0]);
        if (names) {
            return [
                uniq(users.concat(extended_users)).map(i => this.data.rows[i]),
                uniq(permissions.concat(extended_permissions)).map(i => this.data.columns[i]),
            ];
        } else {
            return [
                uniq(users.concat(extended_users)),
                uniq(permissions.concat(extended_permissions)),
            ];
        }
    }

    get_superfluous_assignments(names: boolean = true): number[][] {
        let result = [];
        let users = this.get_role_selection(false)[0];
        let perms = this.get_role_selection(false)[1];
        for (let user in users) {
            for (let perm in perms) {
                if (!this.data.matrix[+users[user]][+perms[perm]]) {
                    result.push([+users[user], +perms[perm]]);
                }
            }
        }
        if (names) {
            let result_names = [];
            for (let assignment in result) {
                let a = result[assignment];
                result_names.push([this.data.rows[a[0]], this.data.columns[a[1]]]);
            }
            return result_names;
        } else {
            return result;
        }
    }

    render(): void {
        this.clear_canvas();
        let frame: string[][] = [];

        // Render the basic visualisation.
        for (let row_n in this.data.matrix) {
            frame[row_n] = [];
            let row = this.data.matrix[row_n];
            for (let cell_n in row) {
                let cell = row[cell_n];
                frame[row_n][cell_n] = cell ? '#000000' : null;
            }
        }

        // Render an overlay.
        if (this.overlay != null) {
            for (let row_n in this.overlay.matrix) {
                let row = this.overlay.matrix[row_n];
                for (let cell_n in row) {
                    let cell = this.data.matrix[row_n][cell_n];
                    let val = row[cell_n];
                    if (cell == false && val > 0) {
                        frame[row_n][cell_n] = '#FF0000';
                    } else if (cell == true && val > 0) {
                        // let mapped = Math.round(map(val, this.overlay_range[0], this.overlay_range[1]/2, 0, 170));
                        // let hex = mapped.toString(16).padStart(2, '0');
                        // frame[row_n][cell_n] = '#' + hex + hex + '00';
                        frame[row_n][cell_n] = '#FFFF00';
                    }
                }
            }
        }

        // Render already selected.
        for (let r in this.already_generated) {
            let role: GeneratedRole = this.already_generated[r];
            for (let u in role.users) {
                let user = role.users[u];
                for (let p in role.permissions) {
                    let perm = role.permissions[p];
                    if (role.render) {
                        frame[user][perm] = frame[user][perm] ? '#0000A0' : '#800080';
                    } else if (user in this.data.rows && perm in this.data.columns) {
                        frame[user][perm] = null;
                    }
                }
            }
        }

        // Render the current selection.
        if (this.selection) {
            let users = range(this.selection[0][1], this.selection[1][1]);
            let perms = range(this.selection[0][0], this.selection[1][0]);
            for (let u in users) {
                let user = users[u];
                for (let p in perms) {
                    let perm = perms[p];
                    frame[user][perm] = frame[user][perm] ? '#7CFC00' : '#FF0000';
                }
            }

            // Render extended selection.
            if (this.extended_selection) {
                for (let u in this.extended_selection[1]) {
                    let user = this.extended_selection[1][u];
                    for (let p in perms) {
                        let perm = perms[p];
                        frame[user][perm] = frame[user][perm] ? '#228B22' : '#8B0000';
                    }
                    for (let p in this.extended_selection[0]) {
                        let perm = this.extended_selection[0][p];
                        frame[user][perm] = frame[user][perm] ? '#228B22' : '#8B0000';
                    }
                }
                for (let p in this.extended_selection[0]) {
                    let perm = this.extended_selection[0][p];
                    for (let u in users) {
                        let user = users[u];
                        frame[user][perm] = frame[user][perm] ? '#228B22' : '#8B0000';
                    }
                }
            }
        }

        if (this.previous_cursor) {
            frame[this.previous_cursor[1]][this.previous_cursor[0]] = '#FFDB00';
        }

        // Write the frame to canvas.
        for (let frame_y in frame) {
            for (let frame_x in frame[frame_y]) {
                let c = frame[frame_y][frame_x];
                if (c == null) {
                    continue;
                } else {
                    this.canvas_context.fillStyle = c;
                }
                this.canvas_context.fillRect(
                    (+frame_x * this.scaling_factor) + this.pan_offset[0],
                    (+frame_y * this.scaling_factor) + this.pan_offset[1],
                    this.scaling_factor,
                    this.scaling_factor
                );
            }
        }

    }

    load_meta_data(data) {

        let meta_user: any[] = [];
        for (let u in data.user) {
            let user: any = data.user[u];
            meta_user[String(user.user)] = user;
        }
        this.meta_user = meta_user;
        this.meta_user_totals = calc_totals_over_group(this.data.rows, this.meta_user);


        let meta_permission: any[] = [];
        for (let p in data.permission) {
            let permission: any = data.permission[p];
            meta_permission[String(permission.permission)] = permission;
        }
        this.meta_permission = meta_permission;
        this.meta_permission_totals = calc_totals_over_group(this.data.columns, this.meta_permission);

    }

    apply_overlay(data: number[][], rows: string[], columns: string[]) {
        this.overlay = new OverlayData(data, rows, columns);

        this.overlay_range = [0, 0];
        for (let row_n in this.overlay.matrix) {
            let row = this.overlay.matrix[row_n];
            for (let cell_n in row) {
                let val = row[cell_n];
                this.overlay_range[0] = Math.min(this.overlay_range[0], val);
                this.overlay_range[1] = Math.max(this.overlay_range[1], val);
            }
        }
    }

    apply_generated_roles(roles: object[]): void {
        for (let r in roles) {

            let role: any = roles[r];

            let data_users: number[] = [];
            let data_perms: number[] = [];

            for (let u in role.users) {
                data_users.push(this.data.rows.indexOf(role.users[u]));
            }
            for (let u in role.permissions) {
                data_perms.push(this.data.columns.indexOf(role.permissions[u]));
            }

            let generated_role = new GeneratedRole(data_users, data_perms, role.render);

            this.already_generated.push(generated_role);

        }
        this.render();
        $("#matrix_loading").remove();
    }

    clear_canvas(): void {
        this.canvas_context.clearRect(0, 0, this.canvas_context.canvas.width, this.canvas_context.canvas.height);
    }

    pan(delta_x: number, delta_y: number): void {
        this.pan_offset[0] += delta_x;
        this.pan_offset[1] += delta_y;

        this.pan_offset[0] = number_bound(this.pan_offset[0], -(this.data.columns.length * this.scaling_factor) + this.canvas_element.width, 0);
        this.pan_offset[1] = number_bound(this.pan_offset[1], -(this.data.rows.length * this.scaling_factor) + this.canvas_element.height, 0);
        this.render();
    }

    pixel_to_cell(mouse_x: number, mouse_y: number): number[] {
        let cell_x = Math.floor((mouse_x - this.pan_offset[0]) / this.scaling_factor);
        let cell_y = Math.floor((mouse_y - this.pan_offset[1]) / this.scaling_factor);

        return [cell_x, cell_y];
    }

    cell_in_selection(cell_x: number, cell_y: number): boolean {
        return number_between(cell_x, this.selection[0][0], this.selection[1][0]) &&
            number_between(cell_y, this.selection[0][1], this.selection[1][1]);
    }

    cell_in_extended_selection(cell_x: number, cell_y: number): boolean {
        return (number_between(cell_x, this.selection[0][0], this.selection[1][0]) &&
            this.extended_selection[1].indexOf(cell_y) >= 0) ||
            (number_between(cell_y, this.selection[0][1], this.selection[1][1]) &&
                this.extended_selection[0].indexOf(cell_x) >= 0) ||
            (this.extended_selection[1].indexOf(cell_y) >= 0 &&
                this.extended_selection[0].indexOf(cell_x) >= 0);
    }

    cell_allready_selected(cell_x: number, cell_y: number): boolean {
        for (let r in this.already_generated) {
            let role: GeneratedRole = this.already_generated[r];
            if (!role.render) {
                continue
            }
            if (role.users.indexOf(cell_y) >= 0 && role.permissions.indexOf(cell_x) >= 0) return true;
        }
        return false;
    }

    cell_do_not_render(cell_x: number, cell_y: number): boolean {
        let container_width = this.canvas_element.width;
        let container_height = this.canvas_element.height;

        let x = (+cell_x * this.scaling_factor) + this.pan_offset[0];
        let y = (+cell_y * this.scaling_factor) + this.pan_offset[1];

        if ((x < -this.scaling_factor || x > container_width) || (y < -this.scaling_factor || y > container_height)) {
            return true;
        }

        for (let r in this.already_generated) {
            let role: GeneratedRole = this.already_generated[r];
            if (role.render) {
                continue
            }
            if (role.users.indexOf(cell_y) >= 0 && role.permissions.indexOf(cell_x) >= 0) return true;
        }
        return false;
    }

    selection_size(): number[] {
        if (this.selection == null) {
            return null;
        } else {
            let selection: string[][] = this.get_role_selection();
            return [
                selection[0].length,
                selection[1].length
            ];
        }
    }

    normalize_selection(): void {
        let x_1 = this.selection[0][0];
        let y_1 = this.selection[0][1];
        let x_2 = this.selection[1][0];
        let y_2 = this.selection[1][1];

        let top_left = [Math.min(x_1, x_2), Math.min(y_1, y_2)];
        let bottom_right = [Math.max(x_1, x_2), Math.max(y_1, y_2)];

        this.selection = [top_left, bottom_right];
    }

    /*
        1: up
        2: right
        3: down
        4: left
     */
    dragging_direction(previous_cell: number[], current_cell: number[]): number {
        let change_in_x = this.cell_in_selection(previous_cell[0], previous_cell[1]) != this.cell_in_selection(current_cell[0], previous_cell[1]);
        if (change_in_x) {
            return previous_cell[0] <= current_cell[0] ? 2 : 4
        } else {
            return previous_cell[1] <= current_cell[1] ? 3 : 1
        }
    }

    mouse_up(): void {
        if (this.is_selecting) {
            this.is_first_selection = false;
            this.normalize_selection();
            this.selection_start = null;
        }
        this.is_panning = false;
        this.is_selecting = false;
        this.is_extending = false;
    }

    mouse_down(e: MouseEvent): void {
        if (e.shiftKey && e.altKey) {
            let cell = this.pixel_to_cell(e.offsetX, e.offsetY);
            this.is_extending = true;
            this.is_extending_adding = !this.cell_in_extended_selection(cell[0], cell[1]);
            return;
        } else if (e.shiftKey) {
            this.is_selecting = true;
            return;
        }
        this.is_panning = true;
    }

    mouse_move(e: MouseEvent): void {
        let cell = this.pixel_to_cell(e.offsetX, e.offsetY);
        if (this.is_panning) {

            this.pan(e.movementX, e.movementY);

        }

        if (this.is_extending) {

            if (!this.is_first_selection && this.cell_in_selection(cell[0], cell[1])) {
                return;
            }

            let axis = -1;
            if (this.selection[0][0] <= cell[0] && cell[0] <= this.selection[1][0]) {
                axis = 1
            } else if (this.selection[0][1] <= cell[1] && cell[1] <= this.selection[1][1]) {
                axis = 0
            }

            if (axis >= 0) {
                let c = cell[axis];
                if (this.is_extending_adding) {
                    this.extended_selection[axis].push(c)
                    this.extended_selection[axis] = uniq(this.extended_selection[axis]);
                } else {
                    this.extended_selection[axis] = this.extended_selection[axis].filter((function (i) {
                        return i != c;
                    }).bind(c));
                }
            }


        } else if (this.is_selecting) {

            if (this.is_first_selection) {

                if (this.selection_start == null) {
                    this.selection_start = cell;
                }

                this.selection = [this.selection_start, cell];
                this.extended_selection = [[], []];

            } else {

                // Selecting
                if (this.cell_in_selection(this.previous_cursor[0], this.previous_cursor[1]) && !this.cell_in_selection(cell[0], cell[1])) {
                    let direction = this.dragging_direction(this.previous_cursor, cell);
                    switch (direction) {
                        case 1: {
                            this.selection = [[this.selection[0][0], cell[1]], [this.selection[1][0], this.selection[1][1]]];
                            break;
                        }
                        case 2: {
                            this.selection = [[this.selection[0][0], this.selection[0][1]], [cell[0], this.selection[1][1]]];
                            break;
                        }
                        case 3: {
                            this.selection = [[this.selection[0][0], this.selection[0][1]], [this.selection[1][0], cell[1]]];
                            break;
                        }
                        case 4: {
                            this.selection = [[cell[0], this.selection[0][1]], [this.selection[1][0], this.selection[1][1]]];
                            break;
                        }
                    }
                }

                // Deselecting
                else if (!this.cell_in_selection(this.previous_cursor[0], this.previous_cursor[1]) && this.cell_in_selection(cell[0], cell[1])) {
                    let direction = this.dragging_direction(this.previous_cursor, cell);
                    switch (direction) {
                        case 1: {
                            this.selection = [[this.selection[0][0], this.selection[0][1]], [this.selection[1][0], cell[1] - 1]];
                            break;
                        }
                        case 2: {
                            this.selection = [[cell[0] + 1, this.selection[0][1]], [this.selection[1][0], this.selection[1][1]]];
                            break;
                        }
                        case 3: {
                            this.selection = [[this.selection[0][0], cell[1] + 1], [this.selection[1][0], this.selection[1][1]]];
                            break;
                        }
                        case 4: {
                            this.selection = [[this.selection[0][0], this.selection[0][1]], [cell[0] - 1, this.selection[1][1]]];
                            break;
                        }
                    }
                }

            }

        }

        this.previous_cursor = [cell[0], cell[1]];
        this.render();

        let permission_name = this.data.columns[cell[0]];
        let permission = (this.meta_permission != null ? this.meta_permission[permission_name] : null);
        permission_name = (permission ? permission.name : permission_name);

        let user_name = this.data.rows[cell[1]];
        let user = (this.meta_user != null ? this.meta_user[user_name] : null);
        user_name = (user ? user.user : user_name);


        $("#matrix_selected_user").html(cell[1] in this.data.rows ? user_name : 'Outside matrix');
        $("#matrix_selected_perm").html(cell[0] in this.data.columns ? permission_name : 'Outside matrix');
        if (this.selection != null) {
            $("#matrix_selection").show();
            let selection_size = this.selection_size();
            $("#matrix_selection_size").html(selection_size[0] + " users, " + selection_size[1] + " permissions");
            if (this.get_superfluous_assignments(false).length > 0) {
                $("#matrix_superfluous_assignments").show();
            } else {
                $("#matrix_superfluous_assignments").hide();
            }
        } else {
            $("#matrix_selection").hide();
        }
    }

    mouse_wheel(e: WheelEvent): void {
        let old_scaling_factor = this.scaling_factor;

        // do the scaling
        let sign = e.deltaY > 0 ? 1 : -1;
        let delta_scale = -sign * Math.pow((number_bound(e.deltaY, -20, 20) / 20), 2);
        this.scaling_factor = number_bound(this.scaling_factor + delta_scale, this.min_scaling_factor, 10);

        // zoom towards current mouse position
        let scale_change = this.scaling_factor - old_scaling_factor;
        this.pan(-(e.offsetX * (scale_change / 2)), -(e.offsetY * (scale_change / 2)));
    }

    key_press(e: KeyboardEvent): void {
        if (this.is_panning || this.is_selecting) {
            return;
        }
        switch (e.key) {
            case 'c': {
                this.selection = null;
                this.selection_start = null;
                this.is_first_selection = true;
                $("#matrix_superfluous_assignments").hide();
                this.render();
                break;
            }
            case 's': {
                this.propose_selection(0);
                break;
            }
            case 'S': {
                this.propose_selection(1);
                break;
            }
            default: {
                break;
            }
        }
    }
}

function number_bound(number: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, number));
}


function number_between(number: number, a: number, b: number, inclusive: boolean = true): boolean {
    let min = Math.min.apply(Math, [a, b]),
        max = Math.max.apply(Math, [a, b]);
    return inclusive ? number >= min && number <= max : number > min && number < max;
}

function uniq(a: number[]): number[] {
    let seen = {};
    return a.filter(function (item) {
        return seen.hasOwnProperty(String(item)) ? false : (seen[item] = true);
    });
}

function range(start: number, end: number): number[] {
    if (start > end) {
        let t = start;
        start = end;
        end = t;
    }
    return Array.apply(null, Array(1 + end - start)).map((function (_, i) {
        return i + start;
    }).bind(start));
}

function map(num: number, in_min: number, in_max: number, out_min: number, out_max: number): number {
    return (num - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

function sparse_length(arr: any[]): number {
    return Object.keys(arr).length;
}

function calc_totals_over_group(list_of_ids: any[], list_of_meta_data: any[]): any[] {
    let meta_totals: any[] = [];
    for (let i in list_of_ids) {
        let item: any = list_of_meta_data[list_of_ids[i]];
        for (let prop in item) {
            if (!item.hasOwnProperty(prop)) {
                continue;
            }
            if (!(prop in meta_totals)) {
                meta_totals[prop] = [];
            }
            if (!(item[prop] in meta_totals[prop])) {
                meta_totals[prop][item[prop]] = 0;
            }
            meta_totals[prop][item[prop]] += 1;
        }
    }
    return meta_totals;
}