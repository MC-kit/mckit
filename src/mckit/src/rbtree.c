#include "rbtree.h"
#include <stdio.h>
#include <stdlib.h>

#define is_left(n) ((n)->parent != NULL && (n)->parent->left == n)
#define is_right(n) ((n)->parent != NULL && (n)->parent->right == n)
#define is_left_red(n) ((n)->left != NULL && (n)->left->color == RED)
#define is_right_red(n) ((n)->right != NULL && (n)->right->color == RED)
#define is_red(n) ((n) != NULL && (n)->color == RED)
#define is_black(n) ((n) != NULL && (n)->color == BLACK)

static void node_init(RBNode *node, RBNode *parent, const void *key);
static RBNode *node_add_balance(RBNode *node);
static RBNode *node_del_balance(RBNode *node);
static RBNode *node_max(RBNode *start);
static RBNode *node_min(RBNode *start);
static void node_free(RBNode *node);
static RBNode *delete_rmin(RBNode *lv, RBNode **root);
static RBNode **node_find(const RBTree *rbt, const void *key, RBNode **parent);
static int rbtree_del(RBTree *rbt, const void *key, RBNode **node);

static void print_node(RBNode *node)
{
    if (node == NULL)
        return;
    char c = node->color == RED ? 'R' : 'B';
    int p = node->parent == NULL ? 0 : *((int *)node->parent->key);
    printf(" %c%dP%d", c, *((int *)node->key), p);
    if (node->left != NULL)
    {
        printf("L(");
        print_node(node->left);
        printf(")");
    }
    if (node->right != NULL)
    {
        printf("R(");
        print_node(node->right);
        printf(")");
    }
}

void rbtree_print(RBTree *rbt)
{
    printf("TREE:\n");
    if (rbt->root != NULL)
        print_node(rbt->root);
    printf("\n");
}

static RBNode **node_find(const RBTree *rbt, const void *key, RBNode **parent)
{
    RBNode **node = (RBNode **)&rbt->root;
    *parent = NULL;
    int comp_res;
    while (*node != NULL)
    {
        comp_res = (*rbt->compare)((*node)->key, key);
        if (comp_res < 0)
        {
            *parent = *node;
            node = &(*node)->left;
        }
        else if (comp_res > 0)
        {
            *parent = *node;
            node = &(*node)->right;
        }
        else
        {
            break;
        }
    }
    return node;
}

RBTree *rbtree_create(int (*compare)(const void *, const void *))
{
    RBTree *rbt = (RBTree *)malloc(sizeof(RBTree));
    if (rbt != NULL)
    {
        rbt->root = NULL;
        rbt->len = 0;
        rbt->compare = compare;
    }
    return rbt;
}

void rbtree_free(RBTree *rbt)
{
    if (rbt != NULL)
    {
        if (rbt->root != NULL)
            node_free(rbt->root);
        free(rbt);
    }
}

const void *rbtree_get(const RBTree *rbt, const void *key)
{
    RBNode *parent;
    RBNode **node = node_find(rbt, key, &parent);
    if (*node != NULL)
        return (*node)->key;
    else
        return NULL;
}

int rbtree_add(RBTree *rbt, const void *key)
{
    RBNode *parent;
    RBNode **node = node_find(rbt, key, &parent);
    if (*node != NULL)
        return RBT_KEY_ALREADY_EXISTS;

    // New node creation
    *node = (RBNode *)malloc(sizeof(RBNode));
    if (*node == NULL)
        return RBT_NO_MEMORY;
    node_init(*node, parent, key);

    if (parent != NULL)
    {
        RBNode *blnc = node_add_balance(parent);
        if (blnc != NULL)
            rbt->root = blnc;
    }

    rbt->len++;

    return RBT_OK;
}

void *rbtree_pop(RBTree *rbt, const void *key)
{
    void *result;
    RBNode *parent, *node;
    if (key == NULL)
        node = rbt->root;
    else
        node = *node_find(rbt, key, &parent);

    if (node == NULL)
        return NULL;

    // find successor for element being deleted.
    RBNode *rmin = delete_rmin(node, &rbt->root);
    // printf("successor for deletion %d\n", *((int *) rmin->key));
    if (rmin == NULL)
    { // if there is no successor, remove element itself.
        RBNode *r = node_del_balance(node);
        if (r != NULL)
            rbt->root = r;

        RBNode *p = node->parent;
        if (p == NULL)
            rbt->root = NULL; // if element being deleted is root.
        else if (p->left == node)
            p->left = NULL; // otherwise delete element
        else
            p->right = NULL; // from successor parent's children list.
    }
    else
    { // if the successor exists,
        if (node != rbt->root)
        {
            if (is_left(node))
                node->parent->left = rmin;
            else
                node->parent->right = rmin;
        }
        else
            rbt->root = rmin;
        rmin->color = node->color;
        rmin->parent = node->parent;
        rmin->left = node->left;
        rmin->right = node->right;
        if (rmin->left != NULL)
            rmin->left->parent = rmin;
        if (rmin->right != NULL)
            rmin->right->parent = rmin;
    }
    result = (void *)node->key;
    free(node);
    rbt->len--;
    return result;
}

static size_t fill_node(const RBNode *node, void *array[], size_t index)
{
    if (node->left != NULL)
        index = fill_node(node->left, array, index);
    array[index++] = (void *)node->key;
    if (node->right != NULL)
        index = fill_node(node->right, array, index);
    return index;
}

void *rbtree_to_array(const RBTree *rbt)
{
    if (rbt->len == 0)
        return NULL;
    void *result = (void *)malloc(rbt->len * sizeof(void *));
    if (result != NULL)
    {
        fill_node(rbt->root, result, 0);
    }
    return result;
}

static void node_init(RBNode *node, RBNode *parent, const void *key)
{
    node->color = RED;
    node->left = NULL;
    node->right = NULL;
    node->parent = parent;
    node->key = key;
}

static RBNode *rotate_left(RBNode *node);
static RBNode *rotate_right(RBNode *node);
static RBNode *flip_colors(RBNode *node);
static RBNode *make_bro_red(RBNode *node);

static RBNode *node_max(RBNode *node)
{
    while (node->right != NULL)
        node = node->right;
    return node;
}

static RBNode *node_min(RBNode *node)
{
    while (node->left != NULL)
        node = node->left;
    return node;
}

/* Finds successor for leave lv.
 *
 * Returns pointer to found successor leave, or NULL if no such leave exists.
 */
static RBNode *delete_rmin(RBNode *lv, RBNode **root)
{
    // Successor is the smallest element in the right branch or the
    // greatest element in the left branch. So if lv->right is not
    // NULL, we will search for smallest element in this branch.
    // Otherwise only one left element can exist and it can be the
    // successor.
    RBNode *rmin = (lv->right != NULL) ? lv->right : lv->left;
    if (rmin == NULL)
        return NULL;

    // If lv->right is NULL then lv->left->left can be only NULL.
    // So in that case this loop won't run.
    while (rmin->left != NULL)
        rmin = rmin->left;

    if (rmin != NULL)
    { // If the successor exists
      // balance the tree.
        RBNode *r = node_del_balance(rmin);
        if (r != NULL)
            *root = r;

        // Then delete successor leave rmin from its parent's children list.
        RBNode *p = rmin->parent;
        if (p->left == rmin)
            p->left = NULL;
        else
            p->right = NULL;
    }
    return rmin;
}

/* Performs balancing of the tree when element added.
 * Balancing starts from the parent (lv) of the just added element.
 *
 * Returns pointer to new root element or NULL if root remains unchanged.
 *
 * Tree balancing procedure consists of the following steps:
 *
 * 1)       |       flip_colors         ||
 *       l==lv==r   ------------>       lv
 *      / \    / \                     /  \
 *                                    l    r
 *                                   / \  / \
 *
 * 2)    |          rotate_left          |
 *       lv==r      ------------>    lv==r
 *      /   / \                     / \   \
 *
 * 3)          |    rotate_right         |
 *      ll==l==lv   ------------>    ll==l==lv
 *     / \   \   \                  / \    / \
 *
 * 4)    parent                  ->  parent
 *         ||     move pointer  /      ||
 *         lv  - - - - - - - - -       lv
 *        /  \                        /  \
 *
 * 5) Otherwise nothing left to do. Remained part is already balanced.
 */
static RBNode *node_add_balance(RBNode *lv)
{
    while (1)
    {
        if (is_red(lv->left) && is_red(lv->right))
        {
            lv = flip_colors(lv);
        }
        else if (is_red(lv->right))
        {
            lv = rotate_left(lv);
        }
        else if (is_red(lv->left) && is_red(lv->left->left))
        {
            lv = rotate_right(lv);
        }
        else if (lv->parent == NULL)
        {
            lv->color = BLACK;
            return lv;
        }
        else if (is_red(lv))
        {
            lv = lv->parent;
        }
        else
        {
            break;
        }
    }
    return NULL;
}

/* Fixes balance of the tree after leave deletion.
 *
 * Returns pointer to the new root struct or NULL if root remains unchanged.
 *
 * 1)     p                             p     if rl is RED           p
 *        |         rotate_left         |     rotate_left            |
 *    *-> lv==r     ============>   lv==r <-* ============>  lv==rl==r
 *       /   / \                   / \   \                  / \   \   \
 *      l   rl  rr                l  rl  rr                l          rr
 *
 * 2)         p                         p
 *            |      rotate_right       |
 *     ll==l==lv <-* ============>      l  <-*
 *    / \   \  \                       / \
 *          lr  r                    ll   lv      FINISH
 *                                  / \  /  \
 *                                      lr   r
 *
 * 3)   parent                 parent
 *        ||                     |
 *    *-> lv         ========>   lv  <-*  FINISH
 *       / \                    / \
 *
 * 4)   parent                 parent <-*
 *      /    \      =======>   //   \
 *    bro    lv <-*           bro   lv
 */
static RBNode *node_del_balance(RBNode *lv)
{
    while (1)
    {
        if (is_red(lv->right))
        {
            lv = rotate_left(lv);
            if (is_red(lv->left->right))
                rotate_left(lv->left);
        }
        else if (is_red(lv->left) && is_red(lv->left->left))
        {
            lv = rotate_right(lv);
            lv->left->color = BLACK;
            lv->right->color = BLACK;
            break;
        }
        else if (is_red(lv))
        {
            lv->color = BLACK;
            break;
        }
        else
        {
            if (lv->parent == NULL)
            {
                lv->color = BLACK;
                return lv;
            }
            lv = make_bro_red(lv);
        }
    }
    if (lv->parent == NULL)
        return lv;
    if (lv->parent->parent == NULL)
        return lv->parent;
    return NULL;
}

/* Makes brother of lv to be red.
 *
 * Returns pointer to lv's parent.
 *
 *        parent           a==parent  <-*
 *        /    \      =>           \
 *       a     lv <-*              lv
 *
 *        parent           *-> parent==a
 *        /    \      =>       /
 *   *-> lv     a             lv
 *
 *          |                       |                           |
 *    a===parent    rotate_right    a===parent   make_bro_red   a===parent <-*
 *   / \       \    ============>  /    /    \   ===========>  /    //   \
 *  al ar      lv <-*             al   ar    lv <-*           al    ar   lv
 */
static RBNode *make_bro_red(RBNode *lv)
{
    RBNode *bro = (lv->parent->left == lv) ? lv->parent->right : lv->parent->left;
    if (is_red(bro))
    {
        rotate_right(lv->parent);
        make_bro_red(lv);
    }
    else
    {
        bro->color = RED;
    }
    return lv->parent;
}

/* Rotates elements left.
 *
 *      ap                  ap
 *      |                   |
 *      a===b     =>    a===b
 *     /   / \         / \   \
 *    al  bl br       al bl  br
 *
 * Returns pointer to b.
 */
static RBNode *rotate_left(RBNode *a)
{
    RBNode *b = a->right; // always there is such member. This function
                          // can be called only in such case. b is not NULL!
    RBNode *bl = b->left;
    RBNode *ap = a->parent; // This can be NULL if a is root.

    a->right = bl;
    if (bl != NULL)
        bl->parent = a;

    b->left = a;
    a->parent = b;
    b->parent = ap;

    int c = a->color;
    a->color = b->color;
    b->color = c;

    if (ap != NULL)
    {
        if (ap->left == a)
            ap->left = b;
        else
            ap->right = b;
    }
    return b;
}

/* Rotates elements right.
 *
 *          bp         bp
 *          |          |
 *      a===b     =>   a===b
 *     / \   \        /   / \
 *    al ar  br      al  ar br
 *
 * Returns pointer to a.
 */
static RBNode *rotate_right(RBNode *b)
{
    RBNode *a = b->left; // a is not NULL.
    RBNode *ar = a->right;
    RBNode *bp = b->parent;

    b->left = ar;
    if (ar != NULL)
        ar->parent = b;

    a->right = b;
    b->parent = a;
    a->parent = bp;

    int c = a->color;
    a->color = b->color;
    b->color = c;

    if (bp != NULL)
    {
        if (bp->left == b)
            bp->left = a;
        else
            bp->right = a;
    }
    return a;
}

/* Flips colors.
 *
 *           ap                     ap
 *           |           =>         ||      <- this link is then rotated
 *    left===nd===right             nd         if necesary.
 *                                 /  \
 *                             left    right
 */
static RBNode *flip_colors(RBNode *node)
{
    node->color = RED;
    node->left->color = BLACK;
    node->right->color = BLACK;
    return node;
}

static void node_free(RBNode *node)
{
    if (node->left != NULL)
        node_free(node->left);
    if (node->right != NULL)
        node_free(node->right);
    free(node);
}
