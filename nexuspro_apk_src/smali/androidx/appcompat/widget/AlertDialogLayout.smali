.class public Landroidx/appcompat/widget/AlertDialogLayout;
.super Landroidx/appcompat/widget/y;
.source "SourceFile"


# direct methods
.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, Landroidx/appcompat/widget/y;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method private g(II)V
    .locals 9

    .line 1
    invoke-virtual {p0}, Landroid/view/View;->getMeasuredWidth()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    const/high16 v1, 0x40000000    # 2.0f

    .line 6
    .line 7
    invoke-static {v0, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 8
    .line 9
    .line 10
    move-result v4

    .line 11
    const/4 v0, 0x0

    .line 12
    :goto_0
    if-ge v0, p1, :cond_1

    .line 13
    .line 14
    invoke-virtual {p0, v0}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 15
    .line 16
    .line 17
    move-result-object v3

    .line 18
    invoke-virtual {v3}, Landroid/view/View;->getVisibility()I

    .line 19
    .line 20
    .line 21
    move-result v1

    .line 22
    const/16 v2, 0x8

    .line 23
    .line 24
    if-eq v1, v2, :cond_0

    .line 25
    .line 26
    invoke-virtual {v3}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 27
    .line 28
    .line 29
    move-result-object v1

    .line 30
    check-cast v1, Landroidx/appcompat/widget/y$a;

    .line 31
    .line 32
    iget v2, v1, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 33
    .line 34
    const/4 v5, -0x1

    .line 35
    if-ne v2, v5, :cond_0

    .line 36
    .line 37
    iget v8, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 38
    .line 39
    invoke-virtual {v3}, Landroid/view/View;->getMeasuredHeight()I

    .line 40
    .line 41
    .line 42
    move-result v2

    .line 43
    iput v2, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 44
    .line 45
    const/4 v5, 0x0

    .line 46
    const/4 v7, 0x0

    .line 47
    move-object v2, p0

    .line 48
    move v6, p2

    .line 49
    invoke-virtual/range {v2 .. v7}, Landroid/view/ViewGroup;->measureChildWithMargins(Landroid/view/View;IIII)V

    .line 50
    .line 51
    .line 52
    iput v8, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 53
    .line 54
    goto :goto_1

    .line 55
    :cond_0
    move v6, p2

    .line 56
    :goto_1
    add-int/lit8 v0, v0, 0x1

    .line 57
    .line 58
    move p2, v6

    .line 59
    goto :goto_0

    .line 60
    :cond_1
    return-void
.end method

.method private v(Landroid/view/View;IIII)V
    .locals 0

    .line 1
    add-int/2addr p4, p2

    .line 2
    add-int/2addr p5, p3

    .line 3
    invoke-virtual {p1, p2, p3, p4, p5}, Landroid/view/View;->layout(IIII)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method private static w(Landroid/view/View;)I
    .locals 3

    .line 1
    invoke-static {p0}, Landroidx/core/view/v;->k(Landroid/view/View;)I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    if-lez v0, :cond_0

    .line 6
    .line 7
    return v0

    .line 8
    :cond_0
    instance-of v0, p0, Landroid/view/ViewGroup;

    .line 9
    .line 10
    const/4 v1, 0x0

    .line 11
    if-eqz v0, :cond_1

    .line 12
    .line 13
    check-cast p0, Landroid/view/ViewGroup;

    .line 14
    .line 15
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 16
    .line 17
    .line 18
    move-result v0

    .line 19
    const/4 v2, 0x1

    .line 20
    if-ne v0, v2, :cond_1

    .line 21
    .line 22
    invoke-virtual {p0, v1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 23
    .line 24
    .line 25
    move-result-object p0

    .line 26
    invoke-static {p0}, Landroidx/appcompat/widget/AlertDialogLayout;->w(Landroid/view/View;)I

    .line 27
    .line 28
    .line 29
    move-result p0

    .line 30
    return p0

    .line 31
    :cond_1
    return v1
.end method

.method private x(II)Z
    .locals 16

    move-object/from16 v0, p0

    move/from16 v1, p1

    move/from16 v2, p2

    .line 1
    invoke-virtual {v0}, Landroid/view/ViewGroup;->getChildCount()I

    move-result v3

    const/4 v4, 0x0

    const/4 v5, 0x0

    move-object v6, v4

    move-object v7, v6

    move v8, v5

    :goto_0
    const/16 v9, 0x8

    if-ge v8, v3, :cond_6

    .line 2
    invoke-virtual {v0, v8}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    move-result-object v10

    .line 3
    invoke-virtual {v10}, Landroid/view/View;->getVisibility()I

    move-result v11

    if-ne v11, v9, :cond_0

    goto :goto_2

    .line 4
    :cond_0
    invoke-virtual {v10}, Landroid/view/View;->getId()I

    move-result v9

    .line 5
    sget v11, Ld/e;->r:I

    if-ne v9, v11, :cond_1

    move-object v4, v10

    goto :goto_2

    .line 6
    :cond_1
    sget v11, Ld/e;->g:I

    if-ne v9, v11, :cond_2

    move-object v6, v10

    goto :goto_2

    .line 7
    :cond_2
    sget v11, Ld/e;->i:I

    if-eq v9, v11, :cond_4

    sget v11, Ld/e;->j:I

    if-ne v9, v11, :cond_3

    goto :goto_1

    :cond_3
    return v5

    :cond_4
    :goto_1
    if-eqz v7, :cond_5

    return v5

    :cond_5
    move-object v7, v10

    :goto_2
    add-int/lit8 v8, v8, 0x1

    goto :goto_0

    .line 8
    :cond_6
    invoke-static {v2}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v8

    .line 9
    invoke-static {v2}, Landroid/view/View$MeasureSpec;->getSize(I)I

    move-result v10

    .line 10
    invoke-static {v1}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v11

    .line 11
    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    move-result v12

    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    move-result v13

    add-int/2addr v12, v13

    if-eqz v4, :cond_7

    .line 12
    invoke-virtual {v4, v1, v5}, Landroid/view/View;->measure(II)V

    .line 13
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredHeight()I

    move-result v13

    add-int/2addr v12, v13

    .line 14
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredState()I

    move-result v4

    invoke-static {v5, v4}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v4

    goto :goto_3

    :cond_7
    move v4, v5

    :goto_3
    if-eqz v6, :cond_8

    .line 15
    invoke-virtual {v6, v1, v5}, Landroid/view/View;->measure(II)V

    .line 16
    invoke-static {v6}, Landroidx/appcompat/widget/AlertDialogLayout;->w(Landroid/view/View;)I

    move-result v13

    .line 17
    invoke-virtual {v6}, Landroid/view/View;->getMeasuredHeight()I

    move-result v14

    sub-int/2addr v14, v13

    add-int/2addr v12, v13

    .line 18
    invoke-virtual {v6}, Landroid/view/View;->getMeasuredState()I

    move-result v15

    invoke-static {v4, v15}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v4

    goto :goto_4

    :cond_8
    move v13, v5

    move v14, v13

    :goto_4
    if-eqz v7, :cond_a

    if-nez v8, :cond_9

    move v15, v5

    goto :goto_5

    :cond_9
    sub-int v15, v10, v12

    .line 19
    invoke-static {v5, v15}, Ljava/lang/Math;->max(II)I

    move-result v15

    .line 20
    invoke-static {v15, v8}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v15

    .line 21
    :goto_5
    invoke-virtual {v7, v1, v15}, Landroid/view/View;->measure(II)V

    .line 22
    invoke-virtual {v7}, Landroid/view/View;->getMeasuredHeight()I

    move-result v15

    add-int/2addr v12, v15

    .line 23
    invoke-virtual {v7}, Landroid/view/View;->getMeasuredState()I

    move-result v5

    invoke-static {v4, v5}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v4

    goto :goto_6

    :cond_a
    const/4 v15, 0x0

    :goto_6
    sub-int/2addr v10, v12

    const/high16 v5, 0x40000000    # 2.0f

    if-eqz v6, :cond_c

    sub-int/2addr v12, v13

    .line 24
    invoke-static {v10, v14}, Ljava/lang/Math;->min(II)I

    move-result v14

    if-lez v14, :cond_b

    sub-int/2addr v10, v14

    add-int/2addr v13, v14

    .line 25
    :cond_b
    invoke-static {v13, v5}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v13

    .line 26
    invoke-virtual {v6, v1, v13}, Landroid/view/View;->measure(II)V

    .line 27
    invoke-virtual {v6}, Landroid/view/View;->getMeasuredHeight()I

    move-result v13

    add-int/2addr v12, v13

    .line 28
    invoke-virtual {v6}, Landroid/view/View;->getMeasuredState()I

    move-result v6

    invoke-static {v4, v6}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v4

    :cond_c
    if-eqz v7, :cond_d

    if-lez v10, :cond_d

    sub-int/2addr v12, v15

    add-int/2addr v15, v10

    .line 29
    invoke-static {v15, v8}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v6

    .line 30
    invoke-virtual {v7, v1, v6}, Landroid/view/View;->measure(II)V

    .line 31
    invoke-virtual {v7}, Landroid/view/View;->getMeasuredHeight()I

    move-result v6

    add-int/2addr v12, v6

    .line 32
    invoke-virtual {v7}, Landroid/view/View;->getMeasuredState()I

    move-result v6

    invoke-static {v4, v6}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v4

    :cond_d
    const/4 v6, 0x0

    const/4 v7, 0x0

    :goto_7
    if-ge v6, v3, :cond_f

    .line 33
    invoke-virtual {v0, v6}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    move-result-object v8

    .line 34
    invoke-virtual {v8}, Landroid/view/View;->getVisibility()I

    move-result v10

    if-eq v10, v9, :cond_e

    .line 35
    invoke-virtual {v8}, Landroid/view/View;->getMeasuredWidth()I

    move-result v8

    invoke-static {v7, v8}, Ljava/lang/Math;->max(II)I

    move-result v7

    :cond_e
    add-int/lit8 v6, v6, 0x1

    goto :goto_7

    .line 36
    :cond_f
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    move-result v6

    invoke-virtual {v0}, Landroid/view/View;->getPaddingRight()I

    move-result v8

    add-int/2addr v6, v8

    add-int/2addr v7, v6

    .line 37
    invoke-static {v7, v1, v4}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v1

    const/4 v4, 0x0

    .line 38
    invoke-static {v12, v2, v4}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v4

    .line 39
    invoke-virtual {v0, v1, v4}, Landroid/view/View;->setMeasuredDimension(II)V

    if-eq v11, v5, :cond_10

    .line 40
    invoke-direct {v0, v3, v2}, Landroidx/appcompat/widget/AlertDialogLayout;->g(II)V

    :cond_10
    const/4 v1, 0x1

    return v1
.end method


# virtual methods
.method protected onLayout(ZIIII)V
    .locals 10

    .line 1
    invoke-virtual {p0}, Landroid/view/View;->getPaddingLeft()I

    .line 2
    .line 3
    .line 4
    move-result p1

    .line 5
    sub-int/2addr p4, p2

    .line 6
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 7
    .line 8
    .line 9
    move-result p2

    .line 10
    sub-int p2, p4, p2

    .line 11
    .line 12
    sub-int/2addr p4, p1

    .line 13
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 14
    .line 15
    .line 16
    move-result v0

    .line 17
    sub-int/2addr p4, v0

    .line 18
    invoke-virtual {p0}, Landroid/view/View;->getMeasuredHeight()I

    .line 19
    .line 20
    .line 21
    move-result v0

    .line 22
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 23
    .line 24
    .line 25
    move-result v1

    .line 26
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->getGravity()I

    .line 27
    .line 28
    .line 29
    move-result v2

    .line 30
    and-int/lit8 v3, v2, 0x70

    .line 31
    .line 32
    const v4, 0x800007

    .line 33
    .line 34
    .line 35
    and-int/2addr v2, v4

    .line 36
    const/16 v4, 0x10

    .line 37
    .line 38
    if-eq v3, v4, :cond_1

    .line 39
    .line 40
    const/16 v4, 0x50

    .line 41
    .line 42
    if-eq v3, v4, :cond_0

    .line 43
    .line 44
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 45
    .line 46
    .line 47
    move-result p3

    .line 48
    goto :goto_0

    .line 49
    :cond_0
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 50
    .line 51
    .line 52
    move-result v3

    .line 53
    add-int/2addr v3, p5

    .line 54
    sub-int/2addr v3, p3

    .line 55
    sub-int p3, v3, v0

    .line 56
    .line 57
    goto :goto_0

    .line 58
    :cond_1
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 59
    .line 60
    .line 61
    move-result v3

    .line 62
    sub-int/2addr p5, p3

    .line 63
    sub-int/2addr p5, v0

    .line 64
    div-int/lit8 p5, p5, 0x2

    .line 65
    .line 66
    add-int p3, v3, p5

    .line 67
    .line 68
    :goto_0
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->getDividerDrawable()Landroid/graphics/drawable/Drawable;

    .line 69
    .line 70
    .line 71
    move-result-object p5

    .line 72
    const/4 v0, 0x0

    .line 73
    if-nez p5, :cond_2

    .line 74
    .line 75
    move p5, v0

    .line 76
    goto :goto_1

    .line 77
    :cond_2
    invoke-virtual {p5}, Landroid/graphics/drawable/Drawable;->getIntrinsicHeight()I

    .line 78
    .line 79
    .line 80
    move-result p5

    .line 81
    :goto_1
    if-ge v0, v1, :cond_8

    .line 82
    .line 83
    invoke-virtual {p0, v0}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 84
    .line 85
    .line 86
    move-result-object v4

    .line 87
    if-eqz v4, :cond_7

    .line 88
    .line 89
    invoke-virtual {v4}, Landroid/view/View;->getVisibility()I

    .line 90
    .line 91
    .line 92
    move-result v3

    .line 93
    const/16 v5, 0x8

    .line 94
    .line 95
    if-eq v3, v5, :cond_7

    .line 96
    .line 97
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredWidth()I

    .line 98
    .line 99
    .line 100
    move-result v7

    .line 101
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredHeight()I

    .line 102
    .line 103
    .line 104
    move-result v8

    .line 105
    invoke-virtual {v4}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 106
    .line 107
    .line 108
    move-result-object v3

    .line 109
    move-object v9, v3

    .line 110
    check-cast v9, Landroidx/appcompat/widget/y$a;

    .line 111
    .line 112
    iget v3, v9, Landroid/widget/LinearLayout$LayoutParams;->gravity:I

    .line 113
    .line 114
    if-gez v3, :cond_3

    .line 115
    .line 116
    move v3, v2

    .line 117
    :cond_3
    invoke-virtual {p0}, Landroid/view/View;->getLayoutDirection()I

    .line 118
    .line 119
    .line 120
    move-result v5

    .line 121
    invoke-static {v3, v5}, Landroidx/core/view/i;->a(II)I

    .line 122
    .line 123
    .line 124
    move-result v3

    .line 125
    and-int/lit8 v3, v3, 0x7

    .line 126
    .line 127
    const/4 v5, 0x1

    .line 128
    if-eq v3, v5, :cond_5

    .line 129
    .line 130
    const/4 v5, 0x5

    .line 131
    if-eq v3, v5, :cond_4

    .line 132
    .line 133
    iget v3, v9, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 134
    .line 135
    add-int/2addr v3, p1

    .line 136
    :goto_2
    move v5, v3

    .line 137
    goto :goto_4

    .line 138
    :cond_4
    sub-int v3, p2, v7

    .line 139
    .line 140
    iget v5, v9, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 141
    .line 142
    :goto_3
    sub-int/2addr v3, v5

    .line 143
    goto :goto_2

    .line 144
    :cond_5
    sub-int v3, p4, v7

    .line 145
    .line 146
    div-int/lit8 v3, v3, 0x2

    .line 147
    .line 148
    add-int/2addr v3, p1

    .line 149
    iget v5, v9, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 150
    .line 151
    add-int/2addr v3, v5

    .line 152
    iget v5, v9, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 153
    .line 154
    goto :goto_3

    .line 155
    :goto_4
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 156
    .line 157
    .line 158
    move-result v3

    .line 159
    if-eqz v3, :cond_6

    .line 160
    .line 161
    add-int/2addr p3, p5

    .line 162
    :cond_6
    iget v3, v9, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 163
    .line 164
    add-int v6, p3, v3

    .line 165
    .line 166
    move-object v3, p0

    .line 167
    invoke-direct/range {v3 .. v8}, Landroidx/appcompat/widget/AlertDialogLayout;->v(Landroid/view/View;IIII)V

    .line 168
    .line 169
    .line 170
    iget p3, v9, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 171
    .line 172
    add-int/2addr v8, p3

    .line 173
    add-int/2addr v6, v8

    .line 174
    move p3, v6

    .line 175
    :cond_7
    add-int/lit8 v0, v0, 0x1

    .line 176
    .line 177
    goto :goto_1

    .line 178
    :cond_8
    return-void
.end method

.method protected onMeasure(II)V
    .locals 1

    .line 1
    invoke-direct {p0, p1, p2}, Landroidx/appcompat/widget/AlertDialogLayout;->x(II)Z

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    if-nez v0, :cond_0

    .line 6
    .line 7
    invoke-super {p0, p1, p2}, Landroidx/appcompat/widget/y;->onMeasure(II)V

    .line 8
    .line 9
    .line 10
    :cond_0
    return-void
.end method
