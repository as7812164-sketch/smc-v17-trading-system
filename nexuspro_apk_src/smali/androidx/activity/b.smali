.class public abstract Landroidx/activity/b;
.super Landroidx/core/app/a;
.source "SourceFile"

# interfaces
.implements Landroidx/lifecycle/j;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/activity/b$a;
    }
.end annotation


# static fields
.field private static final a:Landroidx/activity/b$a;


# direct methods
.method static constructor <clinit>()V
    .locals 2

    new-instance v0, Landroidx/activity/b$a;

    const/4 v1, 0x0

    invoke-direct {v0, v1}, Landroidx/activity/b$a;-><init>(LT/b;)V

    sput-object v0, Landroidx/activity/b;->a:Landroidx/activity/b$a;

    return-void
.end method

.method public static final synthetic b(Landroidx/activity/b;)V
    .locals 0

    .line 1
    const/4 p0, 0x0

    .line 2
    throw p0
.end method
